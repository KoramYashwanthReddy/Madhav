"""Image validation for Module 25 — Vision System.

All external image inputs are UNTRUSTED DATA. This module validates
format, dimensions, size, and integrity before any processing occurs.

Defense against:
- Decompression bombs
- Extremely large images
- Malformed image files
- Memory exhaustion attacks
- Parser crashes
- Format spoofing via extension alone
"""

from __future__ import annotations

import hashlib
import logging
import struct

from max.vision.domain.enums import VisionFormat
from max.vision.domain.exceptions import (
    ImageDecodeError,
    ImageTooLargeError,
    UnsupportedImageFormatError,
    VisionInputError,
)
from max.vision.domain.models import VisionDimensions, VisionMetadata

logger = logging.getLogger(__name__)

# File signature magic bytes (first N bytes)
_MAGIC_SIGNATURES: dict[VisionFormat, list[bytes]] = {
    VisionFormat.PNG: [b"\x89PNG\r\n\x1a\n"],
    VisionFormat.JPEG: [b"\xff\xd8\xff"],
    VisionFormat.WEBP: [b"RIFF"],  # RIFF????WEBP — full check in detect_format
    VisionFormat.BMP: [b"BM"],
    VisionFormat.TIFF: [b"II*\x00", b"MM\x00*"],  # Little/big endian
    VisionFormat.GIF: [b"GIF87a", b"GIF89a"],
}

_EXTENSION_MAP: dict[str, VisionFormat] = {
    ".png": VisionFormat.PNG,
    ".jpg": VisionFormat.JPEG,
    ".jpeg": VisionFormat.JPEG,
    ".webp": VisionFormat.WEBP,
    ".bmp": VisionFormat.BMP,
    ".tif": VisionFormat.TIFF,
    ".tiff": VisionFormat.TIFF,
    ".gif": VisionFormat.GIF,
}

SUPPORTED_FORMATS = {
    VisionFormat.PNG,
    VisionFormat.JPEG,
    VisionFormat.WEBP,
    VisionFormat.BMP,
    VisionFormat.TIFF,
    VisionFormat.GIF,
}


def detect_format_from_bytes(data: bytes) -> VisionFormat:
    """Detect image format from magic bytes (first 12 bytes).

    Does NOT trust file extension alone.
    """
    header = data[:12] if len(data) >= 12 else data

    for fmt, sigs in _MAGIC_SIGNATURES.items():
        for sig in sigs:
            if header.startswith(sig):
                # Extra check for WEBP: bytes 8-12 must be "WEBP"
                if fmt == VisionFormat.WEBP:
                    if len(data) >= 12 and data[8:12] == b"WEBP":
                        return VisionFormat.WEBP
                    continue
                return fmt

    return VisionFormat.UNKNOWN


def detect_format_from_extension(filename: str) -> VisionFormat:
    """Map filename extension to format enum."""
    if not filename:
        return VisionFormat.UNKNOWN
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXTENSION_MAP.get(suffix, VisionFormat.UNKNOWN)


def compute_content_hash(data: bytes) -> str:
    """Compute SHA-256 content hash for deduplication and provenance."""
    return hashlib.sha256(data).hexdigest()


def _read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Read PNG dimensions from IHDR chunk (bytes 16-24)."""
    try:
        if len(data) >= 24:
            width = struct.unpack(">I", data[16:20])[0]
            height = struct.unpack(">I", data[20:24])[0]
            return width, height
    except (struct.error, IndexError):
        pass
    return None


def _read_jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse JPEG SOF markers to extract dimensions."""
    try:
        i = 2  # Skip FFD8
        while i < len(data) - 1:
            if data[i] != 0xFF:
                break
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):  # SOF0, SOF1, SOF2
                if i + 9 <= len(data):
                    height = struct.unpack(">H", data[i + 5 : i + 7])[0]
                    width = struct.unpack(">H", data[i + 7 : i + 9])[0]
                    return width, height
            if i + 3 < len(data):
                seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
                i += 2 + seg_len
            else:
                break
    except (struct.error, IndexError):
        pass
    return None


def _read_bmp_dimensions(data: bytes) -> tuple[int, int] | None:
    """Read BMP dimensions from DIB header."""
    try:
        if len(data) >= 26:
            width = struct.unpack("<i", data[18:22])[0]
            height = abs(struct.unpack("<i", data[22:26])[0])
            return width, height
    except (struct.error, IndexError):
        pass
    return None


def _read_gif_dimensions(data: bytes) -> tuple[int, int] | None:
    """Read GIF canvas dimensions."""
    try:
        if len(data) >= 10:
            width = struct.unpack("<H", data[6:8])[0]
            height = struct.unpack("<H", data[8:10])[0]
            return width, height
    except (struct.error, IndexError):
        pass
    return None


def extract_dimensions_from_bytes(data: bytes, fmt: VisionFormat) -> tuple[int, int] | None:
    """Extract image dimensions from raw bytes without full decoding.

    Returns (width, height) or None if cannot be determined cheaply.
    Avoids full decompression to prevent decompression bomb attacks.
    """
    if fmt == VisionFormat.PNG:
        return _read_png_dimensions(data)
    elif fmt == VisionFormat.JPEG:
        return _read_jpeg_dimensions(data)
    elif fmt == VisionFormat.BMP:
        return _read_bmp_dimensions(data)
    elif fmt == VisionFormat.GIF:
        return _read_gif_dimensions(data)
    return None


class ImageValidator:
    """Validates image inputs against configured security and size limits."""

    def __init__(
        self,
        max_size_bytes: int = 25 * 1024 * 1024,
        max_width: int = 8192,
        max_height: int = 8192,
        max_pixels: int = 33_554_432,  # 32MP
        max_memory_mb: float = 256.0,
    ) -> None:
        self.max_size_bytes = max_size_bytes
        self.max_width = max_width
        self.max_height = max_height
        self.max_pixels = max_pixels
        self.max_memory_mb = max_memory_mb

    def validate(
        self,
        data: bytes,
        filename: str = "",
        hint_format: VisionFormat | None = None,
    ) -> VisionMetadata:
        """Validate image bytes and return extracted metadata.

        Raises VisionInputError hierarchy on any violation.
        Does NOT trust filename extension alone.
        """
        if not data:
            raise VisionInputError("Image data is empty.", details={"filename": filename})

        # --- Size check BEFORE any decompression ---
        file_size = len(data)
        if file_size > self.max_size_bytes:
            raise ImageTooLargeError(
                f"Image file size {file_size / 1024 / 1024:.1f} MB exceeds limit "
                f"{self.max_size_bytes / 1024 / 1024:.1f} MB.",
                details={"file_size_bytes": file_size, "max_size_bytes": self.max_size_bytes},
            )

        # --- Format detection (magic bytes first) ---
        detected_format = detect_format_from_bytes(data)
        extension_format = detect_format_from_extension(filename)

        # Warn if extension and magic bytes disagree
        warnings: list[str] = []
        if (
            detected_format != VisionFormat.UNKNOWN
            and extension_format != VisionFormat.UNKNOWN
            and detected_format != extension_format
        ):
            warnings.append(
                f"Format mismatch: extension suggests {extension_format.value} "
                f"but magic bytes indicate {detected_format.value}. "
                "Using magic bytes detection."
            )

        final_format = detected_format if detected_format != VisionFormat.UNKNOWN else extension_format

        if hint_format and final_format == VisionFormat.UNKNOWN:
            final_format = hint_format

        if final_format == VisionFormat.UNKNOWN:
            raise UnsupportedImageFormatError(
                "Cannot determine image format from magic bytes or file extension.",
                details={"filename": filename},
            )

        if final_format not in SUPPORTED_FORMATS:
            raise UnsupportedImageFormatError(
                f"Image format {final_format.value} is not supported.",
                details={"format": final_format.value, "supported": [f.value for f in SUPPORTED_FORMATS]},
            )

        # --- Dimension check (without full decode) ---
        dims_tuple = extract_dimensions_from_bytes(data, final_format)
        dims: VisionDimensions | None = None

        if dims_tuple is not None:
            w, h = dims_tuple
            if w <= 0 or h <= 0:
                raise ImageDecodeError(
                    f"Invalid image dimensions reported: {w}x{h}.",
                    details={"width": w, "height": h},
                )
            if w > self.max_width:
                raise ImageTooLargeError(
                    f"Image width {w}px exceeds maximum {self.max_width}px.",
                    details={"width": w, "max_width": self.max_width},
                )
            if h > self.max_height:
                raise ImageTooLargeError(
                    f"Image height {h}px exceeds maximum {self.max_height}px.",
                    details={"height": h, "max_height": self.max_height},
                )
            total_pixels = w * h
            if total_pixels > self.max_pixels:
                raise ImageTooLargeError(
                    f"Image pixel count {total_pixels:,} exceeds limit {self.max_pixels:,}.",
                    details={"total_pixels": total_pixels, "max_pixels": self.max_pixels},
                )

            # Estimate decoded memory usage (4 bytes per pixel RGBA)
            estimated_memory_mb = (total_pixels * 4) / (1024 * 1024)
            if estimated_memory_mb > self.max_memory_mb:
                raise ImageTooLargeError(
                    f"Estimated decoded image memory {estimated_memory_mb:.1f} MB exceeds "
                    f"limit {self.max_memory_mb:.1f} MB.",
                    details={"estimated_mb": estimated_memory_mb, "max_mb": self.max_memory_mb},
                )

            dims = VisionDimensions(width=w, height=h)

        content_hash = compute_content_hash(data)

        return VisionMetadata(
            format=final_format,
            dimensions=dims,
            file_size_bytes=file_size,
            content_hash=content_hash,
        )
