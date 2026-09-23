"""Tool trace auditing service."""

import logging
from typing import Any

from madhav.tools.domain.enums import ToolEventType
from madhav.tools.domain.trace import ToolEvent, ToolTrace
from madhav.tools.repositories.trace_repository import (
    BaseToolTraceRepository,
    MemoryToolTraceRepository,
)

logger = logging.getLogger(__name__)


class ToolTraceService:
    """Service for recording and querying immutable tool operational audit traces."""

    def __init__(self, trace_repository: BaseToolTraceRepository | None = None) -> None:
        self.trace_repo = trace_repository or MemoryToolTraceRepository()

    @property
    def repository(self) -> BaseToolTraceRepository:
        return self.trace_repo

    def record_event(
        self,
        event_type: ToolEventType,
        summary: str,
        tool_id: str | None = None,
        invocation_id: str | None = None,
        agent_id: str | None = None,
        run_id: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ToolEvent:
        """Record an immutable operational audit event."""
        event = ToolEvent(
            event_type=event_type,
            summary=summary,
            tool_id=tool_id,
            invocation_id=invocation_id,
            agent_id=agent_id,
            run_id=run_id,
            task_id=task_id,
            metadata=metadata or {},
        )
        saved = self.trace_repo.append_event(event)

        logger.debug(
            "Tool trace event recorded",
            extra={
                "event_id": saved.event_id,
                "event_type": event_type.value,
                "tool_id": tool_id,
                "invocation_id": invocation_id,
            },
        )
        return saved

    def get_trace_for_invocation(self, invocation_id: str) -> ToolTrace:
        """Retrieve aggregated trace events for an invocation."""
        return self.trace_repo.get_trace(invocation_id)

    def get_events_for_tool(self, tool_id: str) -> list[ToolEvent]:
        """Retrieve audit timeline for a tool ID."""
        return self.trace_repo.get_events_for_tool(tool_id)
