"""Tool trace repository interface and thread-safe in-memory implementation."""

import threading
from abc import ABC, abstractmethod

from madhav.tools.domain.trace import ToolEvent, ToolTrace


class BaseToolTraceRepository(ABC):
    """Abstract base repository for ToolTrace audit records."""

    @abstractmethod
    def append_event(self, event: ToolEvent) -> ToolEvent:
        """Append an operational trace event."""
        pass

    @abstractmethod
    def get_events_for_invocation(self, invocation_id: str) -> list[ToolEvent]:
        """Get all trace events for a specific invocation ID."""
        pass

    @abstractmethod
    def get_events_for_tool(self, tool_id: str) -> list[ToolEvent]:
        """Get all trace events for a specific tool ID."""
        pass

    @abstractmethod
    def get_trace(self, invocation_id: str) -> ToolTrace:
        """Get aggregated trace audit record for an invocation."""
        pass


class InMemoryToolTraceRepository(BaseToolTraceRepository):
    """Thread-safe in-memory implementation of ToolTrace persistence."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._events: list[ToolEvent] = []

    def append_event(self, event: ToolEvent) -> ToolEvent:
        with self._lock:
            self._events.append(event)
            return event

    def get_events_for_invocation(self, invocation_id: str) -> list[ToolEvent]:
        with self._lock:
            return [e for e in self._events if e.invocation_id == invocation_id]

    def get_events_for_tool(self, tool_id: str) -> list[ToolEvent]:
        with self._lock:
            return [e for e in self._events if e.tool_id == tool_id]

    def get_trace(self, invocation_id: str) -> ToolTrace:
        with self._lock:
            evts = self.get_events_for_invocation(invocation_id)
            evts.sort(key=lambda e: e.timestamp)
            return ToolTrace(invocation_id=invocation_id, events=evts)


MemoryToolTraceRepository = InMemoryToolTraceRepository
