"""Module 26 — Speech System.

Provides provider-neutral audio capture, validation, voice activity detection,
speech-to-text recognition, text-to-speech synthesis, session management,
barge-in interruption, and tool/API integration for Max Personal AI.
"""

from max.speech.container import SpeechContainer, get_speech_container, reset_speech_container
from max.speech.services.speech_service import SpeechService

__all__ = [
    "SpeechContainer",
    "SpeechService",
    "get_speech_container",
    "reset_speech_container",
]
