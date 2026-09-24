"""In-memory repositories for terminal command execution records and trace events."""

import threading

from max.terminal.domain.models import CommandResult, TerminalSession, TerminalTraceEvent


class CommandExecutionRepository:
    """In-memory store for CommandResult records (execution history)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: dict[str, CommandResult] = {}

    def save(self, result: CommandResult) -> None:
        """Persist a command result record."""
        with self._lock:
            self._records[result.request_id] = result

    def get(self, request_id: str) -> CommandResult | None:
        """Retrieve a command result by request ID."""
        with self._lock:
            return self._records.get(request_id)

    def list_all(self) -> list[CommandResult]:
        """Return all stored command results."""
        with self._lock:
            return list(self._records.values())

    def count(self) -> int:
        """Return the total count of stored records."""
        with self._lock:
            return len(self._records)

    def clear(self) -> None:
        """Clear all records (test isolation helper)."""
        with self._lock:
            self._records.clear()


class TerminalSessionRepository:
    """In-memory store for TerminalSession objects."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, TerminalSession] = {}

    def save(self, session: TerminalSession) -> None:
        """Persist a session record."""
        with self._lock:
            self._sessions[session.session_id] = session

    def get(self, session_id: str) -> TerminalSession | None:
        """Retrieve a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def list_all(self) -> list[TerminalSession]:
        """Return all stored sessions."""
        with self._lock:
            return list(self._sessions.values())

    def count(self) -> int:
        """Return total session count."""
        with self._lock:
            return len(self._sessions)

    def clear(self) -> None:
        """Clear all sessions (test isolation helper)."""
        with self._lock:
            self._sessions.clear()


class TerminalTraceRepository:
    """Append-only in-memory store for TerminalTraceEvent audit records."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: list[TerminalTraceEvent] = []

    def add_event(self, event: TerminalTraceEvent) -> None:
        """Append a new audit trace event."""
        with self._lock:
            self._events.append(event)

    def list_events(
        self,
        request_id: str | None = None,
        event_type: str | None = None,
    ) -> list[TerminalTraceEvent]:
        """Return trace events, optionally filtered by request_id or event_type."""
        with self._lock:
            results = list(self._events)
        if request_id:
            results = [e for e in results if e.request_id == request_id]
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        return results

    def count(self) -> int:
        """Return the total number of trace events."""
        with self._lock:
            return len(self._events)

    def clear(self) -> None:
        """Clear all trace events (test isolation helper)."""
        with self._lock:
            self._events.clear()
