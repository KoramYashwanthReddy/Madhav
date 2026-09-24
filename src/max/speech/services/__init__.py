"""Services package for Module 26 — Speech System."""

from max.speech.services.speech_service import SpeechService
from max.speech.services.tool_integration import register_speech_tools

__all__ = ["SpeechService", "register_speech_tools"]
