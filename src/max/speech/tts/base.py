"""Abstract base class for Text-To-Speech (TTS) providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator

from max.speech.domain.enums import AudioFormat
from max.speech.domain.models import (
    AudioChunk,
    SpeechSynthesisRequest,
    SpeechSynthesisResult,
    Voice,
)


class TextToSpeechProvider(ABC):
    """Provider-neutral Text-To-Speech engine interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical TTS provider identifier."""

    @abstractmethod
    def supports_format(self, fmt: AudioFormat) -> bool:
        """Check if provider supports output audio format."""

    @abstractmethod
    async def synthesize(
        self, request: SpeechSynthesisRequest
    ) -> SpeechSynthesisResult:
        """Synthesize text into complete audio result."""

    @abstractmethod
    async def synthesize_stream(
        self, request: SpeechSynthesisRequest
    ) -> AsyncGenerator[AudioChunk, None]:
        """Stream synthesized audio chunks for real-time playback."""

    @abstractmethod
    def list_voices(self) -> list[Voice]:
        """Return list of available voice models."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities dictionary."""
