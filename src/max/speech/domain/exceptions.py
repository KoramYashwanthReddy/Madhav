"""Domain exceptions for Module 26 — Speech System."""

from typing import Any


class SpeechError(Exception):
    """Base exception for all Speech System errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SpeechInputError(SpeechError):
    """Raised when audio input data or parameters are invalid."""


class AudioDeviceError(SpeechError):
    """Raised when audio input or output device operations fail."""


class AudioPermissionError(SpeechError):
    """Raised when audio access or microphone permission is denied."""


class AudioFormatError(SpeechError):
    """Raised when audio format, codec, or header is unsupported or malformed."""


class AudioTooLargeError(SpeechInputError):
    """Raised when audio payload size exceeds configured limits."""


class AudioTooLongError(SpeechInputError):
    """Raised when audio duration exceeds configured limits."""


class SpeechProviderError(SpeechError):
    """Raised when an STT, TTS, or VAD provider encounters an operational failure."""


class SpeechModelUnavailableError(SpeechProviderError):
    """Raised when requested STT/TTS model is unavailable or unloaded."""


class TranscriptionError(SpeechProviderError):
    """Raised when speech-to-text recognition fails."""


class SynthesisError(SpeechProviderError):
    """Raised when text-to-speech synthesis fails."""


class VoiceNotFoundError(SpeechInputError):
    """Raised when requested voice ID is not found or unsupported."""


class SpeechSessionError(SpeechError):
    """Raised when session state transitions or operations are invalid."""


class SpeechTimeoutError(SpeechError):
    """Raised when a speech operation times out."""


class SpeechCancelledError(SpeechError):
    """Raised when a speech operation or stream is explicitly cancelled."""


class SpeechSecurityError(SpeechError):
    """Raised when security boundaries or audio access policies are violated."""


class BargeInError(SpeechError):
    """Raised when speech interruption processing fails."""
