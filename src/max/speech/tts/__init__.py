"""TTS subpackage for Module 26 — Speech System."""

from max.speech.tts.base import TextToSpeechProvider
from max.speech.tts.local_tts import LocalTextToSpeechProvider
from max.speech.tts.mock_tts import MockTextToSpeechProvider
from max.speech.tts.registry import TextToSpeechProviderRegistry

__all__ = [
    "LocalTextToSpeechProvider",
    "MockTextToSpeechProvider",
    "TextToSpeechProvider",
    "TextToSpeechProviderRegistry",
]
