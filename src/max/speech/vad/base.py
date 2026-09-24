"""Abstract base class for Voice Activity Detection (VAD) providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from max.speech.domain.models import SpeechActivity


class VoiceActivityDetector(ABC):
    """Provider-neutral Voice Activity Detector abstraction.

    Does NOT require an LLM for VAD execution.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical provider identifier."""

    @abstractmethod
    def detect_activity(self, data: bytes, sample_rate: int = 16000) -> SpeechActivity:
        """Analyze audio frame and return structured SpeechActivity model."""

    def detect_speech(self, data: bytes, sample_rate: int = 16000) -> bool:
        """Return True if active speech is detected in frame."""
        act = self.detect_activity(data, sample_rate)
        return act.activity_type.name in ("SPEECH", "POSSIBLE_SPEECH")

    def detect_silence(self, data: bytes, sample_rate: int = 16000) -> bool:
        """Return True if frame is silent."""
        act = self.detect_activity(data, sample_rate)
        return act.activity_type.name == "SILENCE"
