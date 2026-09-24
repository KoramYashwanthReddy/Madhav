"""High-fidelity Mock STT Provider for CI and testing."""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncGenerator

from max.speech.audio.streaming import AudioInputStream
from max.speech.domain.enums import AudioFormat, SpeechProcessingStatus, TranscriptState
from max.speech.domain.models import (
    LanguageDetectionResult,
    SpeechProvenance,
    SpeechRecognitionAlternative,
    SpeechRecognitionRequest,
    SpeechRecognitionResult,
    Transcript,
    TranscriptSegment,
    TranscriptWord,
)
from max.speech.stt.base import SpeechToTextProvider


class MockSpeechToTextProvider(SpeechToTextProvider):
    """High-fidelity mock STT provider returning deterministic structured transcripts."""

    def __init__(self, mock_transcript: str = "Open my VS Code project and start database") -> None:
        self.mock_transcript = mock_transcript

    @property
    def provider_name(self) -> str:
        return "mock"

    def supports_format(self, fmt: AudioFormat) -> bool:
        return True

    async def transcribe(
        self, request: SpeechRecognitionRequest
    ) -> SpeechRecognitionResult:
        start_time = time.monotonic()

        words_raw = self.mock_transcript.split()
        transcript_words: list[TranscriptWord] = []
        cur_t = 0.0
        for w in words_raw:
            dur = max(0.2, len(w) * 0.05)
            transcript_words.append(
                TranscriptWord(
                    word=w,
                    start_time_seconds=round(cur_t, 2),
                    end_time_seconds=round(cur_t + dur, 2),
                    confidence=0.96,
                )
            )
            cur_t += dur

        segment = TranscriptSegment(
            text=self.mock_transcript,
            start_time_seconds=0.0,
            end_time_seconds=round(cur_t, 2),
            confidence=0.96,
            words=transcript_words,
            language=request.language_preference or "en",
        )

        transcript = Transcript(
            session_id=request.session_id,
            raw_text=self.mock_transcript,
            normalized_text=self.mock_transcript,
            language=request.language_preference or "en",
            confidence=0.96,
            segments=[segment],
            words=transcript_words,
            state=TranscriptState.FINAL,
            is_untrusted_data=True,
            processing_duration_seconds=round(time.monotonic() - start_time, 4),
        )

        provenance = SpeechProvenance(
            session_id=request.session_id,
            provider="mock",
            model="mock-stt-v1",
            model_version="1.0.0",
            language=request.language_preference or "en",
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return SpeechRecognitionResult(
            request_id=request.request_id,
            status=SpeechProcessingStatus.COMPLETED,
            transcript=transcript,
            alternatives=[
                SpeechRecognitionAlternative(text=self.mock_transcript, confidence=0.96)
            ],
            provenance=provenance,
            processing_time_ms=elapsed_ms,
        )

    async def transcribe_stream(
        self, stream: AudioInputStream, request: SpeechRecognitionRequest
    ) -> AsyncGenerator[Transcript, None]:
        words = self.mock_transcript.split()
        accumulated_text = ""

        for i, word in enumerate(words):
            if not stream.is_open:
                break

            accumulated_text = (accumulated_text + " " + word).strip()
            is_final = (i == len(words) - 1)

            yield Transcript(
                session_id=request.session_id,
                raw_text=accumulated_text,
                normalized_text=accumulated_text,
                language="en",
                confidence=0.95,
                state=TranscriptState.FINAL if is_final else TranscriptState.PARTIAL,
                is_untrusted_data=True,
            )
            await asyncio.sleep(0.01)

    async def detect_language(self, data: bytes) -> LanguageDetectionResult:
        return LanguageDetectionResult(
            language_code="en",
            language_name="English",
            confidence=0.98,
            alternatives={"en": 0.98, "es": 0.02},
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "models": ["mock-stt-v1"],
            "supports_streaming": True,
            "supports_word_timestamps": True,
            "supports_multilingual": True,
            "supported_formats": [f.value for f in AudioFormat],
        }
