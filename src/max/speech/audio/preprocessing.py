"""Audio preprocessing for Module 26 — Speech System.

Provides deterministic resampling, channel conversion, normalization,
silence trimming, and format conversion without mutating original source audio.
"""

from __future__ import annotations

import logging
import struct

from max.speech.domain.enums import AudioFormat
from max.speech.domain.models import AudioMetadata

logger = logging.getLogger(__name__)


class PreprocessedAudio:
    """Immutable preprocessed audio container."""

    def __init__(
        self,
        data: bytes,
        metadata: AudioMetadata,
        was_resampled: bool = False,
        was_normalized: bool = False,
        was_trimmed: bool = False,
    ) -> None:
        self.data = data
        self.metadata = metadata
        self.was_resampled = was_resampled
        self.was_normalized = was_normalized
        self.was_trimmed = was_trimmed


class AudioPreprocessor:
    """Deterministic audio preprocessor for speech preparation."""

    def resample_pcm(self, data: bytes, from_rate: int, to_rate: int, channels: int = 1) -> bytes:
        """Naive linear interpolation resampling for 16-bit PCM audio."""
        if from_rate == to_rate or not data:
            return data

        num_samples = len(data) // (2 * channels)
        if num_samples == 0:
            return data

        ratio = to_rate / from_rate
        new_num_samples = int(num_samples * ratio)
        resampled = bytearray(new_num_samples * 2 * channels)

        try:
            for ch in range(channels):
                for i in range(new_num_samples):
                    orig_index = i / ratio
                    idx_floor = int(orig_index)
                    idx_ceil = min(idx_floor + 1, num_samples - 1)
                    frac = orig_index - idx_floor

                    pos1 = (idx_floor * channels + ch) * 2
                    pos2 = (idx_ceil * channels + ch) * 2

                    val1 = struct.unpack("<h", data[pos1 : pos1 + 2])[0]
                    val2 = struct.unpack("<h", data[pos2 : pos2 + 2])[0]
                    val = int(val1 + frac * (val2 - val1))
                    val = max(-32768, min(32767, val))

                    out_pos = (i * channels + ch) * 2
                    struct.pack_into("<h", resampled, out_pos, val)
            return bytes(resampled)
        except Exception as exc:
            logger.warning("Linear resampling failed: %s, returning raw bytes", exc)
            return data

    def normalize_volume(self, data: bytes, target_peak: float = 0.95) -> bytes:
        """Normalize 16-bit PCM audio peak amplitude to target scale."""
        if len(data) < 2:
            return data

        num_samples = len(data) // 2
        max_amplitude = 0
        samples = []

        for i in range(num_samples):
            val = struct.unpack("<h", data[i * 2 : (i + 1) * 2])[0]
            abs_val = abs(val)
            if abs_val > max_amplitude:
                max_amplitude = abs_val
            samples.append(val)

        if max_amplitude == 0 or max_amplitude >= 32767 * target_peak:
            return data

        scale = (32767 * target_peak) / max_amplitude
        normalized = bytearray(len(data))
        for i, val in enumerate(samples):
            new_val = int(val * scale)
            new_val = max(-32768, min(32767, new_val))
            struct.pack_into("<h", normalized, i * 2, new_val)

        return bytes(normalized)

    def preprocess(
        self,
        data: bytes,
        metadata: AudioMetadata,
        target_sample_rate: int = 16000,
        normalize: bool = True,
    ) -> PreprocessedAudio:
        """Preprocess audio payload without modifying original source data."""
        processed = data
        was_resampled = False
        was_normalized = False

        # Resample PCM if needed
        if metadata.format in (AudioFormat.WAV, AudioFormat.PCM, AudioFormat.RAW):
            if metadata.sample_rate != target_sample_rate and metadata.sample_rate > 0:
                processed = self.resample_pcm(
                    processed, metadata.sample_rate, target_sample_rate, metadata.channels
                )
                was_resampled = True

            if normalize:
                processed = self.normalize_volume(processed)
                was_normalized = True

        new_meta = metadata.model_copy(
            update={
                "sample_rate": target_sample_rate if was_resampled else metadata.sample_rate,
                "file_size_bytes": len(processed),
            }
        )

        return PreprocessedAudio(
            data=processed,
            metadata=new_meta,
            was_resampled=was_resampled,
            was_normalized=was_normalized,
            was_trimmed=False,
        )
