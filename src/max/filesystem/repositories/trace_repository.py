"""Repository for filesystem audit and security trace events."""

import threading

from max.filesystem.domain.models import FilesystemTraceEvent


class FilesystemTraceRepository:
    """Thread-safe in-memory repository for filesystem audit trace events."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: list[FilesystemTraceEvent] = []

    def add_event(self, event: FilesystemTraceEvent) -> FilesystemTraceEvent:
        """Add a new trace event."""
        with self._lock:
            self._events.append(event)
            return event

    def list_events(
        self,
        operation_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[FilesystemTraceEvent]:
        """List trace events filtered by operation ID or event type."""
        with self._lock:
            results = self._events
            if operation_id is not None:
                results = [e for e in results if e.operation_id == operation_id]
            if event_type is not None:
                results = [e for e in results if e.event_type == event_type]
            results.sort(key=lambda e: e.timestamp, reverse=True)
            return results[:limit]

    def clear(self) -> None:
        """Clear trace events."""
        with self._lock:
            self._events.clear()
