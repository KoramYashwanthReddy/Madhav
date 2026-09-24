"""SpeechService facade — master orchestrator for Module 26 — Speech System.

SpeechService is the single entry point for all speech processing:
callers (agents, tools, API routes, adapters) use this service.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncGenerator

from max.config.sections import SpeechSettings
from max.speech.audio.devices import AudioDeviceRegistry, AudioInputDevice, AudioOutputDevice
from max.speech.audio.preprocessing import AudioPreprocessor, PreprocessedAudio
from max.speech.audio.streaming import AudioInputStream, AudioOutputStream
from max.speech.audio.validation import AudioValidator
from max.speech.domain.enums import (
    AudioFormat,
    InterruptionReason,
    SpeechInputType,
    SpeechProcessingStatus,
    SpeechSessionStatus,
)
from max.speech.domain.exceptions import (
    AudioPermissionError,
    SpeechError,
    SpeechInputError,
    SpeechProviderError,
)
from max.speech.domain.models import (
    AudioChunk,
    AudioMetadata,
    LanguageDetectionResult,
    SpeechActivity,
    SpeechInput,
    SpeechInterruption,
    SpeechRecognitionRequest,
    SpeechRecognitionResult,
    SpeechSession,
    SpeechSynthesisRequest,
    SpeechSynthesisResult,
    Transcript,
    Voice,
    VoiceConfiguration,
)
from max.speech.normalization.transcript_normalizer import TranscriptNormalizer
from max.speech.security.enforcer import SpeechSecurityEnforcer
from max.speech.sessions.manager import SpeechSessionManager
from max.speech.stt.registry import SpeechToTextProviderRegistry
from max.speech.tts.registry import TextToSpeechProviderRegistry
from max.speech.vad.base import VoiceActivityDetector

logger = logging.getLogger(__name__)


class SpeechService:
    """Master facade service orchestrating the full Speech System pipeline."""

    def __init__(
        self,
        settings: SpeechSettings,
        validator: AudioValidator,
        preprocessor: AudioPreprocessor,
        vad_detector: VoiceActivityDetector,
        stt_registry: SpeechToTextProviderRegistry,
        tts_registry: TextToSpeechProviderRegistry,
        session_manager: SpeechSessionManager,
        device_registry: AudioDeviceRegistry,
        security_enforcer: SpeechSecurityEnforcer,
        normalizer: TranscriptNormalizer,
    ) -> None:
        self._settings = settings
        self._validator = validator
        self._preprocessor = preprocessor
        self._vad = vad_detector
        self._stt_registry = stt_registry
        self._tts_registry = tts_registry
        self._session_manager = session_manager
        self._device_registry = device_registry
        self._security = security_enforcer
        self._normalizer = normalizer

    # --- Speech Session Operations ---

    def create_session(
        self,
        owner_id: str = "user_default",
        input_type: SpeechInputType = SpeechInputType.MICROPHONE,
        voice_config: VoiceConfiguration | None = None,
    ) -> SpeechSession:
        """Create a new validated SpeechSession."""
        if input_type == SpeechInputType.MICROPHONE:
            self._security.verify_microphone_permission(owner_id, "LISTEN")
        return self._session_manager.create_session(owner_id, input_type, voice_config)

    def get_session(self, session_id: str) -> SpeechSession:
        """Retrieve SpeechSession by ID."""
        return self._session_manager.get_session(session_id)

    def list_sessions(self, owner_id: str | None = None) -> list[SpeechSession]:
        """List active/historical speech sessions."""
        return self._session_manager.list_sessions(owner_id)

    async def cancel_session(self, session_id: str) -> SpeechSession:
        """Cooperatively cancel an active speech session."""
        return await self._session_manager.cancel_session(session_id)

    async def handle_barge_in(
        self, session_id: str, reason: InterruptionReason = InterruptionReason.USER_SPEECH
    ) -> SpeechInterruption:
        """Process user barge-in interruption."""
        return await self._session_manager.handle_barge_in(session_id, reason)

    # --- Voice Activity Detection ---

    def detect_activity(self, data: bytes, sample_rate: int = 16000) -> SpeechActivity:
        """Perform Voice Activity Detection on raw audio bytes."""
        return self._vad.detect_activity(data, sample_rate)

    # --- Speech-to-Text Recognition ---

    async def transcribe(
        self,
        data: bytes,
        session_id: str = "",
        language: str | None = "en",
        provider_name: str | None = None,
    ) -> SpeechRecognitionResult:
        """Perform full speech-to-text recognition pipeline on audio bytes."""
        start_time = time.monotonic()

        # Validate input
        metadata = self._validator.validate(data)

        # Preprocess input
        preprocessed = self._preprocessor.preprocess(data, metadata)

        # Get STT Provider
        provider = self._stt_registry.get(provider_name or self._settings.default_stt_provider)

        request = SpeechRecognitionRequest(
            session_id=session_id,
            input_data=preprocessed.data,
            metadata=preprocessed.metadata,
            language_preference=language,
        )

        result = await provider.transcribe(request)

        # Normalize transcript & enforce security shielding
        normalized_transcript = self._normalizer.normalize_transcript(result.transcript)
        shielded_transcript = self._security.enforce_transcript_shielding(normalized_transcript)

        # Check prompt injection risk
        if self._security.detect_prompt_injection_risk(shielded_transcript.normalized_text):
            logger.warning("Prompt injection risk detected in speech transcript for session=%s", session_id)

        final_result = result.model_copy(update={"transcript": shielded_transcript})

        # Update session active transcript if associated
        if session_id:
            try:
                sess = self._session_manager.get_session(session_id)
                sess.active_transcript = shielded_transcript
                if sess.status in (SpeechSessionStatus.LISTENING, SpeechSessionStatus.SPEECH_DETECTED, SpeechSessionStatus.TRANSCRIBING):
                    sess.transition_to(SpeechSessionStatus.PROCESSING)
            except SpeechError:
                pass

        return final_result

    async def transcribe_stream(
        self,
        stream: AudioInputStream,
        session_id: str = "",
        language: str | None = "en",
        provider_name: str | None = None,
    ) -> AsyncGenerator[Transcript, None]:
        """Perform real-time streaming speech recognition."""
        provider = self._stt_registry.get(provider_name or self._settings.default_stt_provider)
        request = SpeechRecognitionRequest(session_id=session_id, language_preference=language)

        async for partial_tx in provider.transcribe_stream(stream, request):
            normalized = self._normalizer.normalize_transcript(partial_tx)
            shielded = self._security.enforce_transcript_shielding(normalized)
            yield shielded

    async def detect_language(self, data: bytes) -> LanguageDetectionResult:
        """Detect spoken language from audio payload."""
        provider = self._stt_registry.get(self._settings.default_stt_provider)
        return await provider.detect_language(data)

    # --- Text-to-Speech Synthesis ---

    async def synthesize(
        self,
        text: str,
        session_id: str = "",
        voice_id: str | None = None,
        provider_name: str | None = None,
    ) -> SpeechSynthesisResult:
        """Synthesize text to speech audio result."""
        if not text:
            raise SpeechInputError("Synthesis text cannot be empty.")

        provider = self._tts_registry.get(provider_name or self._settings.default_tts_provider)
        voice_config = VoiceConfiguration(
            voice_id=voice_id or self._settings.default_voice_id,
            provider=provider.provider_name,
        )

        request = SpeechSynthesisRequest(
            session_id=session_id,
            text=text,
            voice_config=voice_config,
        )

        result = await provider.synthesize(request)

        if session_id:
            try:
                sess = self._session_manager.get_session(session_id)
                if sess.status in (SpeechSessionStatus.PROCESSING, SpeechSessionStatus.THINKING, SpeechSessionStatus.SYNTHESIZING):
                    sess.transition_to(SpeechSessionStatus.PLAYING)
            except SpeechError:
                pass

        return result

    async def synthesize_stream(
        self,
        text: str,
        session_id: str = "",
        voice_id: str | None = None,
        provider_name: str | None = None,
    ) -> AsyncGenerator[AudioChunk, None]:
        """Stream synthesized TTS audio chunks for real-time playback."""
        provider = self._tts_registry.get(provider_name or self._settings.default_tts_provider)
        voice_config = VoiceConfiguration(
            voice_id=voice_id or self._settings.default_voice_id,
            provider=provider.provider_name,
        )

        request = SpeechSynthesisRequest(
            session_id=session_id, text=text, voice_config=voice_config, streaming=True
        )

        output_stream = AudioOutputStream(stream_id=f"out_{session_id or 'anon'}")
        await output_stream.open()

        if session_id:
            self._session_manager.register_output_stream(session_id, output_stream)

        async for chunk in provider.synthesize_stream(request):
            if not output_stream.is_open:
                logger.info("Synthesis stream cancelled for session=%s", session_id)
                break
            yield chunk

        await output_stream.close()

    # --- Hardware Devices & Voices ---

    def list_voices(self, provider_name: str | None = None) -> list[Voice]:
        """List available TTS voice models."""
        provider = self._tts_registry.get(provider_name or self._settings.default_tts_provider)
        return provider.list_voices()

    def list_input_devices(self) -> list[AudioInputDevice]:
        """List microphone devices."""
        return self._device_registry.list_input_devices()

    def list_output_devices(self) -> list[AudioOutputDevice]:
        """List speaker devices."""
        return self._device_registry.list_output_devices()
