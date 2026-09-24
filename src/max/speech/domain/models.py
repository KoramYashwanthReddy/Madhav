"""Domain models for Module 26 — Speech System."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.speech.domain.enums import (
    AudioFormat,
    AudioSourceType,
    InterruptionReason,
    SpeechActivityType,
    SpeechEventType,
    SpeechInputType,
    SpeechProcessingStatus,
    SpeechSessionStatus,
    TranscriptState,
    VoiceGender,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class AudioSource(BaseModel):
    """Audio input source descriptor."""

    source_type: AudioSourceType = Field(default=AudioSourceType.MICROPHONE)
    source_reference: str = Field(default="", description="Path, URI, or device ID")
    owner_id: str = Field(default="user_default")


class AudioMetadata(BaseModel):
    """Technical metadata for audio payloads."""

    format: AudioFormat = Field(default=AudioFormat.WAV)
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")
    channels: int = Field(default=1, description="Audio channels count")
    bit_depth: int = Field(default=16, description="Bits per sample")
    duration_seconds: float = Field(default=0.0, ge=0.0)
    file_size_bytes: int = Field(default=0, ge=0)
    audio_hash: str = Field(default="", description="SHA-256 hash for audio integrity")
    codec: str = Field(default="pcm_s16le")
    created_at: datetime = Field(default_factory=_utc_now)


class AudioChunk(BaseModel):
    """Individual chunk of streaming audio bytes."""

    chunk_id: str = Field(default_factory=lambda: _generate_id("achk"))
    session_id: str = Field(default="")
    sequence_number: int = Field(default=0, ge=0)
    data: bytes = Field(default=b"", description="Raw audio chunk bytes")
    sample_rate: int = Field(default=16000)
    channels: int = Field(default=1)
    format: AudioFormat = Field(default=AudioFormat.PCM)
    duration_ms: float = Field(default=0.0, ge=0.0)
    is_last: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=_utc_now)


class AudioStreamConfiguration(BaseModel):
    """Configuration for streaming audio input/output."""

    sample_rate: int = Field(default=16000)
    channels: int = Field(default=1)
    bit_depth: int = Field(default=16)
    format: AudioFormat = Field(default=AudioFormat.PCM)
    chunk_size_bytes: int = Field(default=4096)
    buffer_duration_ms: int = Field(default=100)


class SpeechInput(BaseModel):
    """Container for speech input (files, streams, or raw bytes)."""

    input_id: str = Field(default_factory=lambda: _generate_id("sinp"))
    input_type: SpeechInputType = Field(default=SpeechInputType.MICROPHONE)
    source: AudioSource = Field(default_factory=AudioSource)
    metadata: AudioMetadata = Field(default_factory=AudioMetadata)
    audio_bytes: bytes = Field(default=b"")
    created_at: datetime = Field(default_factory=_utc_now)


class SpeechActivity(BaseModel):
    """Voice Activity Detection observation."""

    activity_id: str = Field(default_factory=lambda: _generate_id("svad"))
    activity_type: SpeechActivityType = Field(default=SpeechActivityType.SILENCE)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    start_time_ms: float = Field(default=0.0, ge=0.0)
    end_time_ms: float = Field(default=0.0, ge=0.0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    energy_level: float = Field(default=0.0, ge=0.0)


class SpeechSegment(BaseModel):
    """Continuous speech utterance segment."""

    segment_id: str = Field(default_factory=lambda: _generate_id("sseg"))
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)
    speaker_tag: str | None = Field(default=None)
    activity: SpeechActivity = Field(default_factory=SpeechActivity)


class TranscriptWord(BaseModel):
    """Word-level timing and confidence detail."""

    word: str
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TranscriptTimestamp(BaseModel):
    """Segment timestamp boundaries."""

    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)


class TranscriptConfidence(BaseModel):
    """Aggregated recognition confidence assessment."""

    score: float = Field(default=0.0, ge=0.0, le=1.0)
    is_high_confidence: bool = Field(default=True)


class TranscriptSegment(BaseModel):
    """Segment of transcribed text with timestamps and word details."""

    segment_id: str = Field(default_factory=lambda: _generate_id("tseg"))
    text: str = Field(default="")
    start_time_seconds: float = Field(default=0.0, ge=0.0)
    end_time_seconds: float = Field(default=0.0, ge=0.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    words: list[TranscriptWord] = Field(default_factory=list)
    speaker: str | None = Field(default=None)
    language: str | None = Field(default="en")


class LanguageDetectionResult(BaseModel):
    """Language identification result."""

    language_code: str = Field(default="en")
    language_name: str = Field(default="English")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    alternatives: dict[str, float] = Field(default_factory=dict)


class Transcript(BaseModel):
    """Master transcript model preserving raw, normalized, and word-level data."""

    transcript_id: str = Field(default_factory=lambda: _generate_id("tx"))
    session_id: str = Field(default="")
    raw_text: str = Field(default="")
    normalized_text: str = Field(default="")
    language: str = Field(default="en")
    language_detection: LanguageDetectionResult | None = Field(default=None)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    segments: list[TranscriptSegment] = Field(default_factory=list)
    words: list[TranscriptWord] = Field(default_factory=list)
    state: TranscriptState = Field(default=TranscriptState.FINAL)
    is_untrusted_data: bool = Field(
        default=True, description="Enforces prompt injection shielding"
    )
    processing_duration_seconds: float = Field(default=0.0, ge=0.0)
    created_at: datetime = Field(default_factory=_utc_now)


class SpeechProvenance(BaseModel):
    """Origin and configuration tracking for speech processing."""

    session_id: str = Field(default="")
    audio_source: AudioSourceType = Field(default=AudioSourceType.MICROPHONE)
    audio_hash: str = Field(default="")
    provider: str = Field(default="mock")
    model: str = Field(default="mock-stt-v1")
    model_version: str = Field(default="1.0.0")
    language: str = Field(default="en")
    timestamp: datetime = Field(default_factory=_utc_now)


class SpeechRecognitionAlternative(BaseModel):
    """Alternative transcript hypothesis from STT engine."""

    text: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    words: list[TranscriptWord] = Field(default_factory=list)


class SpeechRecognitionRequest(BaseModel):
    """Speech-to-text recognition request parameters."""

    request_id: str = Field(default_factory=lambda: _generate_id("sttr"))
    session_id: str = Field(default="")
    input_data: bytes = Field(default=b"")
    metadata: AudioMetadata = Field(default_factory=AudioMetadata)
    language_preference: str | None = Field(default="en")
    model_preference: str | None = Field(default=None)
    enable_word_timestamps: bool = Field(default=True)
    enable_language_detection: bool = Field(default=True)
    multilingual_support: bool = Field(default=True)


class SpeechRecognitionResult(BaseModel):
    """Speech-to-text recognition result."""

    result_id: str = Field(default_factory=lambda: _generate_id("sttres"))
    request_id: str = Field(default="")
    status: SpeechProcessingStatus = Field(default=SpeechProcessingStatus.COMPLETED)
    transcript: Transcript = Field(default_factory=Transcript)
    alternatives: list[SpeechRecognitionAlternative] = Field(default_factory=list)
    provenance: SpeechProvenance = Field(default_factory=SpeechProvenance)
    processing_time_ms: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)


class VoiceCapabilities(BaseModel):
    """Capabilities supported by a TTS voice model."""

    supports_streaming: bool = Field(default=True)
    supports_pitch_adjustment: bool = Field(default=True)
    supports_speed_adjustment: bool = Field(default=True)
    supports_volume_adjustment: bool = Field(default=True)
    supported_formats: list[AudioFormat] = Field(
        default_factory=lambda: [AudioFormat.WAV, AudioFormat.MP3, AudioFormat.PCM]
    )
    supported_sample_rates: list[int] = Field(default_factory=lambda: [16000, 22050, 24000, 44100])


class Voice(BaseModel):
    """TTS voice model representation."""

    voice_id: str
    name: str
    language: str = Field(default="en-US")
    gender: VoiceGender = Field(default=VoiceGender.NEUTRAL)
    provider: str = Field(default="mock")
    model: str = Field(default="mock-tts-v1")
    sample_rate: int = Field(default=22050)
    capabilities: VoiceCapabilities = Field(default_factory=VoiceCapabilities)
    description: str = Field(default="Default synthetic voice")


class VoiceConfiguration(BaseModel):
    """User/Session speech synthesis parameters."""

    voice_id: str = Field(default="mock_voice_en_female")
    language: str = Field(default="en-US")
    speech_rate: float = Field(default=1.0, ge=0.25, le=4.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    output_format: AudioFormat = Field(default=AudioFormat.WAV)
    sample_rate: int = Field(default=22050)
    provider: str = Field(default="mock")


class SpeechSynthesisRequest(BaseModel):
    """Text-to-speech synthesis request."""

    request_id: str = Field(default_factory=lambda: _generate_id("ttsr"))
    session_id: str = Field(default="")
    text: str
    voice_config: VoiceConfiguration = Field(default_factory=VoiceConfiguration)
    streaming: bool = Field(default=False)


class SpeechAudioOutput(BaseModel):
    """Audio data generated by TTS synthesis."""

    audio_bytes: bytes = Field(default=b"")
    metadata: AudioMetadata = Field(default_factory=AudioMetadata)
    voice_id: str = Field(default="mock_voice_en_female")
    provider: str = Field(default="mock")
    model: str = Field(default="mock-tts-v1")


class SpeechSynthesisResult(BaseModel):
    """Text-to-speech synthesis result."""

    result_id: str = Field(default_factory=lambda: _generate_id("ttsres"))
    request_id: str = Field(default="")
    status: SpeechProcessingStatus = Field(default=SpeechProcessingStatus.COMPLETED)
    output: SpeechAudioOutput = Field(default_factory=SpeechAudioOutput)
    duration_seconds: float = Field(default=0.0, ge=0.0)
    processing_time_ms: float = Field(default=0.0, ge=0.0)
    errors: list[str] = Field(default_factory=list)


class SpeechProcessingError(BaseModel):
    """Structured operational error details."""

    error_code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)


class SpeechInterruption(BaseModel):
    """Speech interruption / barge-in event model."""

    interruption_id: str = Field(default_factory=lambda: _generate_id("sint"))
    session_id: str
    reason: InterruptionReason = Field(default=InterruptionReason.USER_SPEECH)
    timestamp: datetime = Field(default_factory=_utc_now)
    stopped_tts_chunk_index: int | None = Field(default=None)


class SpeechEvent(BaseModel):
    """Structured observable speech system event."""

    event_id: str = Field(default_factory=lambda: _generate_id("sevt"))
    session_id: str
    event_type: SpeechEventType
    duration_ms: float | None = Field(default=None)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    status: str | None = Field(default=None)
    error_code: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=_utc_now)


class SpeechSession(BaseModel):
    """First-class Speech Session entity with strict state machine validation."""

    session_id: str = Field(default_factory=lambda: _generate_id("ssess"))
    owner_id: str = Field(default="user_default")
    status: SpeechSessionStatus = Field(default=SpeechSessionStatus.CREATED)
    voice_config: VoiceConfiguration = Field(default_factory=VoiceConfiguration)
    input_type: SpeechInputType = Field(default=SpeechInputType.MICROPHONE)
    active_transcript: Transcript | None = Field(default=None)
    current_interruption: SpeechInterruption | None = Field(default=None)
    error: SpeechProcessingError | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    def transition_to(self, target_status: SpeechSessionStatus) -> None:
        """Validate state transition according to official lifecycle rules."""
        valid_transitions: dict[SpeechSessionStatus, set[SpeechSessionStatus]] = {
            SpeechSessionStatus.CREATED: {
                SpeechSessionStatus.INITIALIZING,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.INITIALIZING: {
                SpeechSessionStatus.LISTENING,
                SpeechSessionStatus.PROCESSING,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.LISTENING: {
                SpeechSessionStatus.SPEECH_DETECTED,
                SpeechSessionStatus.PROCESSING,
                SpeechSessionStatus.PAUSED,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.SPEECH_DETECTED: {
                SpeechSessionStatus.TRANSCRIBING,
                SpeechSessionStatus.PROCESSING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.PROCESSING: {
                SpeechSessionStatus.TRANSCRIBING,
                SpeechSessionStatus.THINKING,
                SpeechSessionStatus.SYNTHESIZING,
                SpeechSessionStatus.PLAYING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.TRANSCRIBING: {
                SpeechSessionStatus.THINKING,
                SpeechSessionStatus.SYNTHESIZING,
                SpeechSessionStatus.LISTENING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.THINKING: {
                SpeechSessionStatus.SYNTHESIZING,
                SpeechSessionStatus.PLAYING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.SYNTHESIZING: {
                SpeechSessionStatus.PLAYING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.PLAYING: {
                SpeechSessionStatus.LISTENING,
                SpeechSessionStatus.INTERRUPTED,
                SpeechSessionStatus.PAUSED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.INTERRUPTED: {
                SpeechSessionStatus.LISTENING,
                SpeechSessionStatus.PROCESSING,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.PAUSED: {
                SpeechSessionStatus.LISTENING,
                SpeechSessionStatus.CANCELLED,
                SpeechSessionStatus.COMPLETED,
                SpeechSessionStatus.FAILED,
            },
            SpeechSessionStatus.COMPLETED: set(),
            SpeechSessionStatus.CANCELLED: set(),
            SpeechSessionStatus.FAILED: set(),
        }

        allowed = valid_transitions.get(self.status, set())
        if target_status not in allowed and target_status != self.status:
            from max.speech.domain.exceptions import SpeechSessionError

            raise SpeechSessionError(
                f"Invalid session state transition from '{self.status.value}' to '{target_status.value}'.",
                details={"current_status": self.status.value, "target_status": target_status.value},
            )

        self.status = target_status
        self.updated_at = _utc_now()
