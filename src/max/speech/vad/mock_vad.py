"""Mock VAD Provider for development and automated testing."""

from __future__ import annotations

import struct

from max.speech.domain.enums import SpeechActivityType
from max.speech.domain.models import SpeechActivity
from max.speech.vad.base import VoiceActivityDetector


class MockVADProvider(VoiceActivityDetector):
    """Deterministic Mock VAD provider inspecting signal RMS energy."""

    def __init__(self, force_speech: bool = False) -> None:
        self._force_speech = force_speech

    @property
    def provider_name(self) -> str:
        return "mock"

    def detect_activity(self, data: bytes, sample_rate: int = 16000) -> SpeechActivity:
        if self._force_speech:
            return SpeechActivity(
                activity_type=SpeechActivityType.SPEECH,
                confidence=0.98,
                start_time_ms=0.0,
                end_time_ms=1000.0,
                duration_ms=1000.0,
                energy_level=0.85,
            )

        if not data or len(data) < 2:
            return SpeechActivity(
                activity_type=SpeechActivityType.SILENCE,
                confidence=1.0,
                start_time_ms=0.0,
                end_time_ms=0.0,
                duration_ms=0.0,
                energy_level=0.0,
            )

        # Compute RMS amplitude for 16-bit PCM
        num_samples = len(data) // 2
        total_sq = 0
        for i in range(num_samples):
            val = struct.unpack("<h", data[i * 2 : (i + 1) * 2])[0]
            total_sq += val * val

        rms = (total_sq / num_samples) ** 0.5
        norm_energy = min(1.0, rms / 10000.0)

        activity_type = (
            SpeechActivityType.SPEECH if norm_energy > 0.05 else SpeechActivityType.SILENCE
        )

        duration_ms = (num_samples / sample_rate) * 1000.0 if sample_rate else 0.0

        return SpeechActivity(
            activity_type=activity_type,
            confidence=0.95 if norm_energy > 0.05 else 0.99,
            start_time_ms=0.0,
            end_time_ms=duration_ms,
            duration_ms=duration_ms,
            energy_level=round(norm_energy, 4),
        )
