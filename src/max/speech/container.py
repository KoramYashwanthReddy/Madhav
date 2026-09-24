"""Dependency Injection container for Module 26 — Speech System."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.speech.audio.devices import AudioDeviceRegistry
from max.speech.audio.preprocessing import AudioPreprocessor
from max.speech.audio.validation import AudioValidator
from max.speech.normalization.transcript_normalizer import TranscriptNormalizer
from max.speech.security.enforcer import SpeechSecurityEnforcer
from max.speech.services.speech_service import SpeechService
from max.speech.services.tool_integration import register_speech_tools
from max.speech.sessions.manager import SpeechSessionManager
from max.speech.stt.local_stt import LocalSpeechToTextProvider
from max.speech.stt.mock_stt import MockSpeechToTextProvider
from max.speech.stt.registry import SpeechToTextProviderRegistry
from max.speech.tts.local_tts import LocalTextToSpeechProvider
from max.speech.tts.mock_tts import MockTextToSpeechProvider
from max.speech.tts.registry import TextToSpeechProviderRegistry
from max.speech.vad.mock_vad import MockVADProvider

logger = logging.getLogger(__name__)


class SpeechContainer:
    """Dependency Injection container managing components of Module 26 — Speech System."""

    def __init__(self) -> None:
        self.settings = get_settings().speech

        self.validator = AudioValidator(
            max_size_mb=self.settings.max_audio_size_mb,
            max_duration_seconds=self.settings.max_audio_duration_seconds,
            max_channels=self.settings.max_channels,
        )
        self.preprocessor = AudioPreprocessor()
        self.vad_detector = MockVADProvider()

        # STT Registry
        self.stt_registry = SpeechToTextProviderRegistry()
        mock_stt = MockSpeechToTextProvider()
        local_stt = LocalSpeechToTextProvider()
        self.stt_registry.register(mock_stt, set_as_default=True)
        self.stt_registry.register(local_stt)

        # TTS Registry
        self.tts_registry = TextToSpeechProviderRegistry()
        mock_tts = MockTextToSpeechProvider()
        local_tts = LocalTextToSpeechProvider()
        self.tts_registry.register(mock_tts, set_as_default=True)
        self.tts_registry.register(local_tts)

        self.session_manager = SpeechSessionManager()
        self.device_registry = AudioDeviceRegistry()
        self.security_enforcer = SpeechSecurityEnforcer(microphone_enabled=self.settings.enabled)
        self.normalizer = TranscriptNormalizer()

        # Master Facade Service
        self.service = SpeechService(
            settings=self.settings,
            validator=self.validator,
            preprocessor=self.preprocessor,
            vad_detector=self.vad_detector,
            stt_registry=self.stt_registry,
            tts_registry=self.tts_registry,
            session_manager=self.session_manager,
            device_registry=self.device_registry,
            security_enforcer=self.security_enforcer,
            normalizer=self.normalizer,
        )

        # Tool registration with M14 Tool Registry
        try:
            from max.tools.services.registry import ToolRegistryService
            register_speech_tools(ToolRegistryService())
        except Exception as exc:
            logger.debug("M14 ToolRegistry auto-registration deferred or skipped: %s", exc)


_SPEECH_CONTAINER_INSTANCE: SpeechContainer | None = None


def get_speech_container() -> SpeechContainer:
    """Get global SpeechContainer singleton instance."""
    global _SPEECH_CONTAINER_INSTANCE
    if _SPEECH_CONTAINER_INSTANCE is None:
        _SPEECH_CONTAINER_INSTANCE = SpeechContainer()
    return _SPEECH_CONTAINER_INSTANCE


def reset_speech_container() -> None:
    """Reset global SpeechContainer instance for test isolation."""
    global _SPEECH_CONTAINER_INSTANCE
    _SPEECH_CONTAINER_INSTANCE = None
