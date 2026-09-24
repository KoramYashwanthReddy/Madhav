"""FastAPI router for Module 26 — Speech System."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from max.speech.container import get_speech_container
from max.speech.domain.enums import AudioFormat, InterruptionReason, SpeechInputType, SpeechSessionStatus
from max.speech.domain.exceptions import (
    AudioDeviceError,
    AudioFormatError,
    AudioPermissionError,
    AudioTooLargeError,
    AudioTooLongError,
    BargeInError,
    SpeechError,
    SpeechInputError,
    SpeechModelUnavailableError,
    SpeechProviderError,
    SpeechSessionError,
    SynthesisError,
    TranscriptionError,
    VoiceNotFoundError,
)

router = APIRouter(prefix="/speech", tags=["Speech System"])


# ---------------------------------------------------------------------------
# API Request / Response Schemas
# ---------------------------------------------------------------------------


class CreateSessionRequest(BaseModel):
    owner_id: str = "user_default"
    input_type: SpeechInputType = SpeechInputType.MICROPHONE
    voice_id: str = "mock_voice_en_female"


class TranscribeRequest(BaseModel):
    audio_bytes_hex: str = Field(description="Hex-encoded raw or container audio bytes")
    session_id: str = ""
    language: str = "en"
    provider: str | None = None


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, description="Text string to speak")
    session_id: str = ""
    voice_id: str = "mock_voice_en_female"
    provider: str | None = None


class BargeInRequest(BaseModel):
    reason: InterruptionReason = InterruptionReason.USER_SPEECH


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_hex(hex_str: str, field_name: str = "audio_bytes_hex") -> bytes:
    """Decode hex-encoded audio bytes; raise 422 on bad format."""
    try:
        return bytes.fromhex(hex_str)
    except ValueError:
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail=f"Invalid hex encoding in field '{field_name}'.",
        )


def _handle_speech_error(exc: Exception) -> None:
    """Map speech exceptions to FastAPI HTTP responses."""
    if isinstance(exc, AudioPermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, (AudioTooLargeError, AudioTooLongError)):
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    if isinstance(exc, AudioFormatError):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    if isinstance(exc, (SpeechInputError, VoiceNotFoundError)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, SpeechSessionError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, SpeechModelUnavailableError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, SpeechError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Speech System subsystem health status."""
    container = get_speech_container()
    return {
        "status": "healthy",
        "subsystem": "speech_system",
        "enabled": container.settings.enabled,
        "stt_enabled": container.settings.stt_enabled,
        "tts_enabled": container.settings.tts_enabled,
        "vad_enabled": container.settings.vad_enabled,
    }


@router.get("/capabilities", status_code=status.HTTP_200_OK)
async def list_capabilities() -> dict[str, Any]:
    """Return supported speech system capabilities."""
    container = get_speech_container()
    return {
        "stt_providers": container.stt_registry.list_providers(),
        "tts_providers": container.tts_registry.list_providers(),
        "default_stt_provider": container.settings.default_stt_provider,
        "default_tts_provider": container.settings.default_tts_provider,
        "streaming_enabled": container.settings.streaming_enabled,
        "barge_in_enabled": container.settings.barge_in_enabled,
        "max_audio_size_mb": container.settings.max_audio_size_mb,
        "max_audio_duration_seconds": container.settings.max_audio_duration_seconds,
    }


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest) -> dict[str, Any]:
    """Create a new SpeechSession."""
    try:
        container = get_speech_container()
        session = container.service.create_session(
            owner_id=request.owner_id,
            input_type=request.input_type,
        )
        return session.model_dump()
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def get_session(session_id: str) -> dict[str, Any]:
    """Retrieve details for a specific SpeechSession."""
    try:
        container = get_speech_container()
        session = container.service.get_session(session_id)
        return session.model_dump()
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.post("/sessions/{session_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_session(session_id: str) -> dict[str, Any]:
    """Cancel an active SpeechSession."""
    try:
        container = get_speech_container()
        session = await container.service.cancel_session(session_id)
        return session.model_dump()
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.post("/sessions/{session_id}/barge-in", status_code=status.HTTP_200_OK)
async def barge_in(session_id: str, request: BargeInRequest) -> dict[str, Any]:
    """Trigger barge-in interruption for an active session."""
    try:
        container = get_speech_container()
        interruption = await container.service.handle_barge_in(session_id, request.reason)
        return interruption.model_dump()
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.post("/transcribe", status_code=status.HTTP_200_OK)
async def transcribe(request: TranscribeRequest) -> dict[str, Any]:
    """Transcribe audio bytes to text."""
    try:
        container = get_speech_container()
        raw_bytes = _decode_hex(request.audio_bytes_hex)
        result = await container.service.transcribe(
            data=raw_bytes,
            session_id=request.session_id,
            language=request.language,
            provider_name=request.provider,
        )
        return result.model_dump()
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.post("/synthesize", status_code=status.HTTP_200_OK)
async def synthesize(request: SynthesizeRequest) -> dict[str, Any]:
    """Synthesize text into speech audio bytes."""
    try:
        container = get_speech_container()
        result = await container.service.synthesize(
            text=request.text,
            session_id=request.session_id,
            voice_id=request.voice_id,
            provider_name=request.provider,
        )
        payload = result.model_dump()
        payload["output"]["audio_bytes_hex"] = result.output.audio_bytes.hex()
        payload["output"].pop("audio_bytes", None)
        return payload
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.get("/voices", status_code=status.HTTP_200_OK)
async def list_voices(provider: str | None = Query(default=None)) -> dict[str, Any]:
    """List available text-to-speech voice models."""
    try:
        container = get_speech_container()
        voices = container.service.list_voices(provider)
        return {"voices": [v.model_dump() for v in voices]}
    except Exception as exc:
        _handle_speech_error(exc)
        return {}


@router.get("/devices", status_code=status.HTTP_200_OK)
async def list_devices() -> dict[str, Any]:
    """List hardware microphone and speaker devices."""
    try:
        container = get_speech_container()
        in_devs = container.service.list_input_devices()
        out_devs = container.service.list_output_devices()
        return {
            "input_devices": [d.model_dump() for d in in_devs],
            "output_devices": [d.model_dump() for d in out_devs],
        }
    except Exception as exc:
        _handle_speech_error(exc)
        return {}
