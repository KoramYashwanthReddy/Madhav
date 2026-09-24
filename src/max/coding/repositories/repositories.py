"""In-memory repository abstractions for Module 22 — Coding Agent."""

import logging

from max.coding.domain.models import ChangeSet, CodingAuditEvent, CodingSession

logger = logging.getLogger(__name__)


class CodingSessionRepository:
    """In-memory repository for active Coding Agent sessions."""

    def __init__(self) -> None:
        self._sessions: dict[str, CodingSession] = {}

    def save(self, session: CodingSession) -> None:
        self._sessions[session.id] = session

    def get(self, session_id: str) -> CodingSession | None:
        return self._sessions.get(session_id)

    def list_all(self, owner_id: str | None = None) -> list[CodingSession]:
        sessions = list(self._sessions.values())
        if owner_id:
            sessions = [s for s in sessions if s.request.owner_id == owner_id]
        return sessions

    def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


class ChangeSetRepository:
    """In-memory repository for change sets."""

    def __init__(self) -> None:
        self._changesets: dict[str, ChangeSet] = {}

    def save(self, changeset: ChangeSet) -> None:
        self._changesets[changeset.id] = changeset

    def get(self, changeset_id: str) -> ChangeSet | None:
        return self._changesets.get(changeset_id)

    def list_by_session(self, session_id: str) -> list[ChangeSet]:
        return [cs for cs in self._changesets.values() if cs.session_id == session_id]


class CodingAuditRepository:
    """In-memory repository for audit event logging."""

    def __init__(self) -> None:
        self._events: list[CodingAuditEvent] = []

    def log_event(self, event: CodingAuditEvent) -> None:
        self._events.append(event)
        logger.info(f"CodingAudit [{event.session_id}] {event.event_type}: {event.details}")

    def list_by_session(self, session_id: str) -> list[CodingAuditEvent]:
        return [e for e in self._events if e.session_id == session_id]
