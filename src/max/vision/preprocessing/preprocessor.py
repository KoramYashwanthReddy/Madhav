"""Image preprocessing pipeline for Module 25 — Vision System.

Preprocessing is deterministic and does NOT modify the original input.
Supports resizing, orientation normalization, grayscale, and cropping.

Dependencies: Uses Pillow (PIL) if available; falls back to passthrough
for environments where PIL is not installed.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

from max.vision.domain.enums import VisionColorSpace, VisionFormat
from max.vision.domain.exceptions import ImageDecodeError
from max.vision.domain.models import VisionBoundingBox, VisionDimensions, VisionProcessingOptions

logger = logging.getLogger(__name__)

try:
    from PIL import Image as PILImage
    from PIL import ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning(
        "Pillow not installed — image preprocessing will be limited to passthrough mode. "
        "Install with: pip install Pillow"
    )


@dataclass
class PreprocessedImage:
    """Result of preprocessing — normalized image bytes + metadata."""

    data: bytes
    width: int
    height: int
    format: VisionFormat
    color_space: VisionColorSpace
    was_resized: bool = False
    was_rotated: bool = False
    was_cropped: bool = False
    was_converted: bool = False
    original_width: int = 0
    original_height: int = 0


def _format_to_pil_mode(color_space: VisionColorSpace) -> str:
    mapping = {
        VisionColorSpace.RGB: "RGB",
        VisionColorSpace.RGBA: "RGBA",
        VisionColorSpace.GRAYSCALE: "L",
        VisionColorSpace.CMYK: "CMYK",
        VisionColorSpace.YCbCr: "YCbCr",
    }
    return mapping.get(color_space, "RGB")


def _pil_mode_to_color_space(mode: str) -> VisionColorSpace:
    mapping = {
        "RGB": VisionColorSpace.RGB,
        "RGBA": VisionColorSpace.RGBA,
        "L": VisionColorSpace.GRAYSCALE,
        "CMYK": VisionColorSpace.CMYK,
        "YCbCr": VisionColorSpace.YCbCr,
        "LA": VisionColorSpace.RGBA,
        "P": VisionColorSpace.RGB,
    }
    return mapping.get(mode, VisionColorSpace.UNKNOWN)


def _vision_format_to_pil(fmt: VisionFormat) -> str:
    mapping = {
        VisionFormat.PNG: "PNG",
        VisionFormat.JPEG: "JPEG",
        VisionFormat.WEBP: "WEBP",
        VisionFormat.BMP: "BMP",
        VisionFormat.TIFF: "TIFF",
    }
    return mapping.get(fmt, "PNG")


class ImagePreprocessor:
    """Deterministic image preprocessing pipeline.

    Follows the pipeline:
    INPUT → VALIDATE → DECODE → NORMALIZE → ORIENTATION →
    OPTIONAL RESIZE → OPTIONAL CROP → MODEL PROCESSING →
    NORMALIZE RESULT → VALIDATE RESULT → RETURN

    Does NOT modify the original input bytes.
    """

    def preprocess(
        self,
        data: bytes,
        fmt: VisionFormat,
        options: VisionProcessingOptions | None = None,
    ) -> PreprocessedImage:
        """Apply deterministic preprocessing to image bytes.

        If Pillow is not installed, returns passthrough result.
        """
        if options is None:
            options = VisionProcessingOptions()

        if not PIL_AVAILABLE:
            logger.debug("Pillow unavailable — passthrough preprocessing.")
            return PreprocessedImage(
                data=data,
                width=0,
                height=0,
                format=fmt,
                color_space=VisionColorSpace.UNKNOWN,
            )

        try:
            return self._preprocess_with_pil(data, fmt, options)
        except Exception as exc:
            raise ImageDecodeError(
                f"Failed to decode/preprocess image: {exc}",
                details={"format": fmt.value},
            ) from exc

    def _preprocess_with_pil(
        self,
        data: bytes,
        fmt: VisionFormat,
        options: VisionProcessingOptions,
    ) -> PreprocessedImage:
        """PIL-based preprocessing implementation."""
        img = PILImage.open(io.BytesIO(data))

        original_width, original_height = img.size
        was_resized = False
        was_rotated = False
        was_cropped = False
        was_converted = False

        # Normalize orientation using EXIF (prevents upside-down images)
        if options.normalize_orientation:
            try:
                img = ImageOps.exif_transpose(img)
                if img.size != (original_width, original_height):
                    was_rotated = True
            except Exception:
                pass  # EXIF transposition is best-effort

        # Force grayscale if requested
        if options.force_grayscale and img.mode != "L":
            img = img.convert("L")
            was_converted = True

        # Explicit rotation
        if options.rotate_degrees is not None and options.rotate_degrees != 0:
            img = img.rotate(-options.rotate_degrees, expand=True)
            was_rotated = True

        # Crop region (applied before resize)
        if options.crop_region is not None:
            box = options.crop_region
            left = int(box.x)
            top = int(box.y)
            right = int(box.x + box.width)
            bottom = int(box.y + box.height)
            # Clamp to image bounds
            left = max(0, min(left, img.width))
            top = max(0, min(top, img.height))
            right = max(left + 1, min(right, img.width))
            bottom = max(top + 1, min(bottom, img.height))
            img = img.crop((left, top, right, bottom))
            was_cropped = True

        # Resize to max dimension (preserving aspect ratio)
        if options.resize_to_max_dimension is not None:
            max_dim = options.resize_to_max_dimension
            if max_dim > 0 and (img.width > max_dim or img.height > max_dim):
                if img.width >= img.height:
                    new_w = max_dim
                    new_h = max(1, int(img.height * max_dim / img.width))
                else:
                    new_h = max_dim
                    new_w = max(1, int(img.width * max_dim / img.height))
                img = img.resize((new_w, new_h), PILImage.LANCZOS)
                was_resized = True

        # Ensure RGB for JPEG output (JPEG doesn't support RGBA)
        pil_fmt = _vision_format_to_pil(fmt)
        if pil_fmt == "JPEG" and img.mode in ("RGBA", "P", "LA"):
            background = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(img, mask=img.split()[-1] if "A" in img.mode else None)
            img = background
            was_converted = True

        # Save back to bytes
        buf = io.BytesIO()
        save_kwargs: dict[str, Any] = {}
        if pil_fmt == "JPEG":
            save_kwargs["quality"] = 95
        img.save(buf, format=pil_fmt, **save_kwargs)
        result_bytes = buf.getvalue()

        return PreprocessedImage(
            data=result_bytes,
            width=img.width,
            height=img.height,
            format=fmt,
            color_space=_pil_mode_to_color_space(img.mode),
            was_resized=was_resized,
            was_rotated=was_rotated,
            was_cropped=was_cropped,
            was_converted=was_converted,
            original_width=original_width,
            original_height=original_height,
        )

    def get_color_space_from_bytes(self, data: bytes) -> VisionColorSpace:
        """Detect color space from image bytes using PIL."""
        if not PIL_AVAILABLE:
            return VisionColorSpace.UNKNOWN
        try:
            img = PILImage.open(io.BytesIO(data))
            return _pil_mode_to_color_space(img.mode)
        except Exception:
            return VisionColorSpace.UNKNOWN
