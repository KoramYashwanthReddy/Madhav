"""VAD subpackage for Module 26 — Speech System."""

from max.speech.vad.base import VoiceActivityDetector
from max.speech.vad.mock_vad import MockVADProvider
from max.speech.vad.states import VADStateMachine

__all__ = [
    "MockVADProvider",
    "VADStateMachine",
    "VoiceActivityDetector",
]
