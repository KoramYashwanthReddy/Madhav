"""Speech Session lifecycle manager and interruption/barge-in orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from max.speech.audio.streaming import AudioOutputStream
from max.speech.domain.enums import InterruptionReason, SpeechInputType, SpeechSessionStatus
from max.speech.domain.exceptions import BargeInError, SpeechSessionError
from max.speech.domain.models import SpeechInterruption, SpeechSession, VoiceConfiguration

logger = logging.getLogger(__name__)


class SpeechSessionManager:
    """Manages speech session entities, state transitions, and barge-in interruptions."""

    def __init__(self) -> None:
        self._sessions: dict[str, SpeechSession] = {}
        self._output_streams: dict[str, AudioOutputStream] = {}

    def create_session(
        self,
        owner_id: str = "user_default",
        input_type: SpeechInputType = SpeechInputType.MICROPHONE,
        voice_config: VoiceConfiguration | None = None,
    ) -> SpeechSession:
        """Create and register a new SpeechSession."""
        session = SpeechSession(
            owner_id=owner_id,
            input_type=input_type,
            voice_config=voice_config or VoiceConfiguration(),
            status=SpeechSessionStatus.CREATED,
        )
        self._sessions[session.session_id] = session
        logger.info("Created SpeechSession id=%s for owner=%s", session.session_id, owner_id)
        return session

    def get_session(self, session_id: str) -> SpeechSession:
        """Retrieve registered SpeechSession by ID."""
        if session_id not in self._sessions:
            raise SpeechSessionError(f"SpeechSession '{session_id}' not found.")
        return self._sessions[session_id]

    def list_sessions(self, owner_id: str | None = None) -> list[SpeechSession]:
        """List active or historical speech sessions."""
        if owner_id:
            return [s for s in self._sessions.values() if s.owner_id == owner_id]
        return list(self._sessions.values())

    def update_status(self, session_id: str, new_status: SpeechSessionStatus) -> SpeechSession:
        """Transition session to new status enforcing state machine constraints."""
        session = self.get_session(session_id)
        session.transition_to(new_status)
        logger.debug("SpeechSession id=%s transitioned to %s", session_id, new_status.value)
        return session

    def register_output_stream(self, session_id: str, stream: AudioOutputStream) -> None:
        """Register active audio output stream for barge-in control."""
        self._output_streams[session_id] = stream

    async def handle_barge_in(
        self, session_id: str, reason: InterruptionReason = InterruptionReason.USER_SPEECH
    ) -> SpeechInterruption:
        """Process user speech barge-in: stop TTS playback stream immediately."""
        session = self.get_session(session_id)

        interruption = SpeechInterruption(session_id=session_id, reason=reason)
        session.current_interruption = interruption

        # Cancel registered output playback stream
        stream = self._output_streams.get(session_id)
        if stream:
            await stream.cancel()
            self._output_streams.pop(session_id, None)

        # Transition state machine
        if session.status in (
            SpeechSessionStatus.PLAYING,
            SpeechSessionStatus.SYNTHESIZING,
            SpeechSessionStatus.PROCESSING,
            SpeechSessionStatus.LISTENING,
        ):
            session.transition_to(SpeechSessionStatus.INTERRUPTED)

        logger.info("SpeechSession id=%s interrupted by barge-in (reason=%s)", session_id, reason.value)
        return interruption

    async def cancel_session(self, session_id: str) -> SpeechSession:
        """Cooperatively cancel an active speech session and all associated streams."""
        session = self.get_session(session_id)

        stream = self._output_streams.pop(session_id, None)
        if stream:
            await stream.cancel()

        if session.status not in (SpeechSessionStatus.COMPLETED, SpeechSessionStatus.CANCELLED, SpeechSessionStatus.FAILED):
            session.transition_to(SpeechSessionStatus.CANCELLED)

        logger.info("SpeechSession id=%s cancelled.", session_id)
        return session
