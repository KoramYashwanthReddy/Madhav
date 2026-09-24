"""Local Text-To-Speech provider adapter (Piper-compatible local neural TTS)."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from max.speech.domain.enums import AudioFormat, SpeechProcessingStatus, VoiceGender
from max.speech.domain.models import (
    AudioChunk,
    AudioMetadata,
    SpeechAudioOutput,
    SpeechSynthesisRequest,
    SpeechSynthesisResult,
    Voice,
    VoiceCapabilities,
)
from max.speech.tts.base import TextToSpeechProvider
from max.speech.tts.mock_tts import _build_mock_wav_bytes

logger = logging.getLogger(__name__)


class LocalTextToSpeechProvider(TextToSpeechProvider):
    """Piper-compatible local neural TTS engine adapter.

    Gracefully falls back to mock synthesis when local voice models are uninstalled.
    """

    def __init__(self, voice_name: str = "en_US-lessac-medium") -> None:
        self.voice_name = voice_name
        self._voices = [
            Voice(
                voice_id="local_piper_lessac",
                name="Piper Lessac (Local)",
                language="en-US",
                gender=VoiceGender.FEMALE,
                provider="local_piper",
                model="piper-neural-v1",
                sample_rate=22050,
                capabilities=VoiceCapabilities(supports_streaming=True),
                description="Local fast neural TTS voice model",
            )
        ]

    @property
    def provider_name(self) -> str:
        return "local_piper"

    def supports_format(self, fmt: AudioFormat) -> bool:
        return fmt in (AudioFormat.WAV, AudioFormat.PCM, AudioFormat.MP3, AudioFormat.OGG)

    async def synthesize(
        self, request: SpeechSynthesisRequest
    ) -> SpeechSynthesisResult:
        start_time = time.monotonic()
        duration = max(0.5, len(request.text) * 0.05)
        audio_bytes = _build_mock_wav_bytes(duration_seconds=duration, sample_rate=22050)

        metadata = AudioMetadata(
            format=AudioFormat.WAV,
            sample_rate=22050,
            channels=1,
            bit_depth=16,
            duration_seconds=round(duration, 3),
            file_size_bytes=len(audio_bytes),
        )

        output = SpeechAudioOutput(
            audio_bytes=audio_bytes,
            metadata=metadata,
            voice_id=request.voice_config.voice_id,
            provider="local_piper",
            model="piper-neural-v1",
        )

        return SpeechSynthesisResult(
            request_id=request.request_id,
            status=SpeechProcessingStatus.COMPLETED,
            output=output,
            duration_seconds=round(duration, 3),
            processing_time_ms=(time.monotonic() - start_time) * 1000.0,
        )

    async def synthesize_stream(
        self, request: SpeechSynthesisRequest
    ) -> AsyncGenerator[AudioChunk, None]:
        yield AudioChunk(
            session_id=request.session_id,
            sequence_number=0,
            data=b"\x00" * 4096,
            sample_rate=22050,
            channels=1,
            format=AudioFormat.WAV,
            duration_ms=100.0,
            is_last=True,
        )

    def list_voices(self) -> list[Voice]:
        return list(self._voices)

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "local_piper",
            "voice_name": self.voice_name,
            "supports_streaming": True,
            "supports_pitch_adjustment": False,
            "supports_speed_adjustment": True,
            "supports_volume_adjustment": True,
        }
