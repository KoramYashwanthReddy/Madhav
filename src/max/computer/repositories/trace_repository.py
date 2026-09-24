"""In-memory repository for computer control operational trace events."""

import threading

from max.computer.domain.models import ComputerTraceEvent


class ComputerTraceRepository:
    """In-memory audit trace repository for computer action events."""

    def __init__(self) -> None:
        self._events: list[ComputerTraceEvent] = []
        self._lock = threading.RLock()

    def record(self, event: ComputerTraceEvent) -> ComputerTraceEvent:
        """Record an operational trace event."""
        with self._lock:
            self._events.append(event)
            return event

    def list_events(
        self,
        action_id: str | None = None,
        sequence_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ComputerTraceEvent]:
        """List recorded trace events matching filters."""
        with self._lock:
            results = list(self._events)
            if action_id:
                results = [e for e in results if e.action_id == action_id]
            if sequence_id:
                results = [e for e in results if e.sequence_id == sequence_id]
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[:limit]

    def clear(self) -> None:
        """Clear trace events."""
        with self._lock:
            self._events.clear()
