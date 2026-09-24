"""High-fidelity Mock TTS Provider for CI and testing."""

from __future__ import annotations

import asyncio
import struct
import time
from typing import Any, AsyncGenerator

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


def _build_mock_wav_bytes(duration_seconds: float = 1.0, sample_rate: int = 22050) -> bytes:
    """Generate valid RIFF WAV audio bytes containing a gentle synthetic sine wave."""
    num_samples = int(duration_seconds * sample_rate)
    pcm_data = bytearray(num_samples * 2)

    # 440Hz sine wave tone
    import math
    for i in range(num_samples):
        t = i / sample_rate
        val = int(3000 * math.sin(2 * math.pi * 440 * t))
        struct.pack_into("<h", pcm_data, i * 2, val)

    data_size = len(pcm_data)
    file_size = 36 + data_size

    header = bytearray()
    header.extend(b"RIFF")
    header.extend(struct.pack("<I", file_size))
    header.extend(b"WAVE")
    header.extend(b"fmt ")
    header.extend(struct.pack("<I", 16))  # Subchunk1Size
    header.extend(struct.pack("<H", 1))   # PCM format
    header.extend(struct.pack("<H", 1))   # Mono channels
    header.extend(struct.pack("<I", sample_rate))
    header.extend(struct.pack("<I", sample_rate * 2))  # Byte rate
    header.extend(struct.pack("<H", 2))   # Block align
    header.extend(struct.pack("<H", 16))  # Bits per sample
    header.extend(b"data")
    header.extend(struct.pack("<I", data_size))

    return bytes(header + pcm_data)


class MockTextToSpeechProvider(TextToSpeechProvider):
    """High-fidelity Mock TTS provider generating valid synthetic WAV audio."""

    def __init__(self) -> None:
        self._voices = [
            Voice(
                voice_id="mock_voice_en_female",
                name="Mock Female Voice",
                language="en-US",
                gender=VoiceGender.FEMALE,
                provider="mock",
                model="mock-tts-v1",
                sample_rate=22050,
                capabilities=VoiceCapabilities(supports_streaming=True),
                description="Default female mock voice for testing",
            ),
            Voice(
                voice_id="mock_voice_en_male",
                name="Mock Male Voice",
                language="en-US",
                gender=VoiceGender.MALE,
                provider="mock",
                model="mock-tts-v1",
                sample_rate=22050,
                capabilities=VoiceCapabilities(supports_streaming=True),
                description="Male mock voice for testing",
            ),
            Voice(
                voice_id="mock_voice_en_neutral",
                name="Mock Neutral Voice",
                language="en-US",
                gender=VoiceGender.NEUTRAL,
                provider="mock",
                model="mock-tts-v1",
                sample_rate=22050,
                capabilities=VoiceCapabilities(supports_streaming=True),
                description="Neutral mock voice for testing",
            ),
        ]

    @property
    def provider_name(self) -> str:
        return "mock"

    def supports_format(self, fmt: AudioFormat) -> bool:
        return True

    async def synthesize(
        self, request: SpeechSynthesisRequest
    ) -> SpeechSynthesisResult:
        start_time = time.monotonic()
        text_length = len(request.text)
        duration = max(0.5, text_length * 0.05)

        audio_bytes = _build_mock_wav_bytes(duration_seconds=duration, sample_rate=request.voice_config.sample_rate)

        metadata = AudioMetadata(
            format=request.voice_config.output_format,
            sample_rate=request.voice_config.sample_rate,
            channels=1,
            bit_depth=16,
            duration_seconds=round(duration, 3),
            file_size_bytes=len(audio_bytes),
            codec="pcm_s16le",
        )

        output = SpeechAudioOutput(
            audio_bytes=audio_bytes,
            metadata=metadata,
            voice_id=request.voice_config.voice_id,
            provider="mock",
            model="mock-tts-v1",
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return SpeechSynthesisResult(
            request_id=request.request_id,
            status=SpeechProcessingStatus.COMPLETED,
            output=output,
            duration_seconds=round(duration, 3),
            processing_time_ms=elapsed_ms,
        )

    async def synthesize_stream(
        self, request: SpeechSynthesisRequest
    ) -> AsyncGenerator[AudioChunk, None]:
        text_length = len(request.text)
        num_chunks = max(2, text_length // 10)

        for i in range(num_chunks):
            chunk_data = b"\x00" * 2048
            is_last = (i == num_chunks - 1)

            yield AudioChunk(
                session_id=request.session_id,
                sequence_number=i,
                data=chunk_data,
                sample_rate=request.voice_config.sample_rate,
                channels=1,
                format=request.voice_config.output_format,
                duration_ms=50.0,
                is_last=is_last,
            )
            await asyncio.sleep(0.01)

    def list_voices(self) -> list[Voice]:
        return list(self._voices)

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "models": ["mock-tts-v1"],
            "supports_streaming": True,
            "supports_pitch_adjustment": True,
            "supports_speed_adjustment": True,
            "supports_volume_adjustment": True,
            "voices_count": len(self._voices),
        }
