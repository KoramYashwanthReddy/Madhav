"""STT subpackage for Module 26 — Speech System."""

from max.speech.stt.base import SpeechToTextProvider
from max.speech.stt.local_stt import LocalSpeechToTextProvider
from max.speech.stt.mock_stt import MockSpeechToTextProvider
from max.speech.stt.registry import SpeechToTextProviderRegistry

__all__ = [
    "LocalSpeechToTextProvider",
    "MockSpeechToTextProvider",
    "SpeechToTextProvider",
    "SpeechToTextProviderRegistry",
]
