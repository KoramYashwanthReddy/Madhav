"""Abstract base class for Speech-To-Text (STT) providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator

from max.speech.audio.streaming import AudioInputStream
from max.speech.domain.enums import AudioFormat
from max.speech.domain.models import (
    LanguageDetectionResult,
    SpeechRecognitionRequest,
    SpeechRecognitionResult,
    Transcript,
)


class SpeechToTextProvider(ABC):
    """Provider-neutral Speech-To-Text engine interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical STT provider identifier."""

    @abstractmethod
    def supports_format(self, fmt: AudioFormat) -> bool:
        """Check if provider supports the given audio format."""

    @abstractmethod
    async def transcribe(
        self, request: SpeechRecognitionRequest
    ) -> SpeechRecognitionResult:
        """Perform non-streaming transcription of an audio payload."""

    @abstractmethod
    async def transcribe_stream(
        self, stream: AudioInputStream, request: SpeechRecognitionRequest
    ) -> AsyncGenerator[Transcript, None]:
        """Perform real-time streaming transcription of an AudioInputStream."""

    @abstractmethod
    async def detect_language(self, data: bytes) -> LanguageDetectionResult:
        """Identify language from audio samples."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return engine metadata and capabilities dictionary."""
