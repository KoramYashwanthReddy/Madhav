"""Audio validation for Module 26 — Speech System.

Validates sample rate, channels, bit depth, duration, format, file size,
and audio payload integrity before any STT or VAD processing occurs.
"""

from __future__ import annotations

import hashlib
import logging
import struct

from max.speech.domain.enums import AudioFormat
from max.speech.domain.exceptions import (
    AudioFormatError,
    AudioTooLargeError,
    AudioTooLongError,
    SpeechInputError,
)
from max.speech.domain.models import AudioMetadata

logger = logging.getLogger(__name__)

# Magic byte signatures for audio formats
_MAGIC_SIGNATURES: dict[AudioFormat, list[bytes]] = {
    AudioFormat.WAV: [b"RIFF"],  # RIFF????WAVE
    AudioFormat.MP3: [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    AudioFormat.OGG: [b"OggS"],
    AudioFormat.FLAC: [b"fLaC"],
    AudioFormat.WEBM: [b"\x1a\x45\xdf\xa3"],  # EBML header
    AudioFormat.M4A: [b"ftypM4A", b"ftypmp42", b"ftypisom"],  # inside ftyp box
}

_EXTENSION_MAP: dict[str, AudioFormat] = {
    ".wav": AudioFormat.WAV,
    ".pcm": AudioFormat.PCM,
    ".mp3": AudioFormat.MP3,
    ".m4a": AudioFormat.M4A,
    ".ogg": AudioFormat.OGG,
    ".webm": AudioFormat.WEBM,
    ".flac": AudioFormat.FLAC,
    ".raw": AudioFormat.RAW,
}

SUPPORTED_AUDIO_FORMATS = {
    AudioFormat.WAV,
    AudioFormat.PCM,
    AudioFormat.MP3,
    AudioFormat.M4A,
    AudioFormat.OGG,
    AudioFormat.WEBM,
    AudioFormat.FLAC,
    AudioFormat.RAW,
}


def detect_format_from_bytes(data: bytes) -> AudioFormat:
    """Detect audio format from header magic bytes."""
    if len(data) < 4:
        return AudioFormat.UNKNOWN

    header = data[:12]

    # WAV check: RIFF...WAVE
    if header.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WAVE":
        return AudioFormat.WAV

    # OGG, FLAC, WEBM
    for fmt in (AudioFormat.OGG, AudioFormat.FLAC, AudioFormat.WEBM):
        for sig in _MAGIC_SIGNATURES[fmt]:
            if header.startswith(sig):
                return fmt

    # MP3 check
    for sig in _MAGIC_SIGNATURES[AudioFormat.MP3]:
        if header.startswith(sig):
            return AudioFormat.MP3

    # M4A check (bytes 4-12 often contain ftyp)
    if len(data) >= 12 and b"ftyp" in data[:16]:
        return AudioFormat.M4A

    return AudioFormat.RAW if len(data) > 0 else AudioFormat.UNKNOWN


def detect_format_from_extension(filename: str) -> AudioFormat:
    """Map filename extension to AudioFormat enum."""
    if not filename:
        return AudioFormat.UNKNOWN
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXTENSION_MAP.get(suffix, AudioFormat.UNKNOWN)


def compute_audio_hash(data: bytes) -> str:
    """Compute SHA-256 content hash for deduplication and audit trail."""
    return hashlib.sha256(data).hexdigest()


def _parse_wav_header(data: bytes) -> tuple[int, int, int, float]:
    """Parse RIFF WAV header to extract (sample_rate, channels, bit_depth, duration)."""
    if len(data) < 44 or not data.startswith(b"RIFF") or data[8:12] != b"WAVE":
        raise AudioFormatError("Invalid or truncated WAV header.")

    try:
        channels = struct.unpack("<H", data[22:24])[0]
        sample_rate = struct.unpack("<I", data[24:28])[0]
        bit_depth = struct.unpack("<H", data[34:36])[0]

        # Locate data chunk
        offset = 12
        data_size = len(data) - 44
        while offset < len(data) - 8:
            chunk_id = data[offset : offset + 4]
            chunk_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]
            if chunk_id == b"data":
                data_size = chunk_size
                break
            offset += 8 + chunk_size + (chunk_size % 2)

        bytes_per_sample = (bit_depth // 8) * channels
        duration = data_size / (sample_rate * bytes_per_sample) if bytes_per_sample and sample_rate else 0.0
        return sample_rate, channels, bit_depth, max(0.0, duration)
    except Exception as exc:
        raise AudioFormatError(f"Failed to parse WAV header: {exc}") from exc


class AudioValidator:
    """Validates incoming audio streams and byte payloads against security and limit rules."""

    def __init__(
        self,
        max_size_mb: float = 25.0,
        max_duration_seconds: float = 600.0,
        max_channels: int = 2,
    ) -> None:
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.max_duration_seconds = max_duration_seconds
        self.max_channels = max_channels

    def validate(
        self,
        data: bytes,
        filename: str | None = None,
        expected_format: AudioFormat | None = None,
    ) -> AudioMetadata:
        """Validate raw audio bytes and return AudioMetadata descriptor."""
        if not data:
            raise SpeechInputError("Audio payload is empty (0 bytes).")

        if len(data) > self.max_size_bytes:
            raise AudioTooLargeError(
                f"Audio payload size ({len(data)} bytes) exceeds limit of {self.max_size_bytes} bytes.",
                details={"size_bytes": len(data), "max_size_bytes": self.max_size_bytes},
            )

        fmt = expected_format
        if fmt is None or fmt in (AudioFormat.UNKNOWN, AudioFormat.RAW):
            fmt = detect_format_from_bytes(data)
            if fmt == AudioFormat.UNKNOWN and filename:
                fmt = detect_format_from_extension(filename)

        if fmt not in SUPPORTED_AUDIO_FORMATS and fmt != AudioFormat.UNKNOWN:
            raise AudioFormatError(
                f"Unsupported audio format '{fmt.value}'. Supported: {[f.value for f in SUPPORTED_AUDIO_FORMATS]}.",
                details={"format": fmt.value},
            )

        sample_rate = 16000
        channels = 1
        bit_depth = 16
        duration = 0.0

        if fmt == AudioFormat.WAV:
            sample_rate, channels, bit_depth, duration = _parse_wav_header(data)
        else:
            # Estimate raw PCM / fallback duration (assuming 16-bit 16kHz mono)
            bytes_per_second = sample_rate * channels * (bit_depth // 8)
            duration = len(data) / bytes_per_second if bytes_per_second else 0.0

        if channels > self.max_channels:
            raise AudioFormatError(
                f"Audio channel count ({channels}) exceeds max allowed ({self.max_channels}).",
                details={"channels": channels, "max_channels": self.max_channels},
            )

        if duration > self.max_duration_seconds:
            raise AudioTooLongError(
                f"Audio duration ({duration:.2f}s) exceeds max allowed ({self.max_duration_seconds}s).",
                details={"duration": duration, "max_duration": self.max_duration_seconds},
            )

        audio_hash = compute_audio_hash(data)

        return AudioMetadata(
            format=fmt,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=bit_depth,
            duration_seconds=round(duration, 3),
            file_size_bytes=len(data),
            audio_hash=audio_hash,
            codec="pcm_s16le" if fmt in (AudioFormat.WAV, AudioFormat.PCM, AudioFormat.RAW) else fmt.value.lower(),
        )
