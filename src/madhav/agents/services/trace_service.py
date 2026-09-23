"""Agent trace logging service for recording operational events (NO chain-of-thought)."""

from typing import Any

from madhav.agents.domain.enums import AgentEventType
from madhav.agents.domain.trace import AgentEvent, AgentTrace
from madhav.agents.repositories.trace_repository import (
    BaseAgentTraceRepository,
    MemoryAgentTraceRepository,
)


class AgentTraceService:
    """Service for appending and retrieving operational agent event traces."""

    def __init__(self, trace_repo: BaseAgentTraceRepository | None = None) -> None:
        self.trace_repo = trace_repo or MemoryAgentTraceRepository()

    def record_event(
        self,
        event_type: AgentEventType,
        agent_id: str,
        summary: str,
        run_id: str | None = None,
        task_id: str | None = None,
        step_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentEvent:
        """Record an operational trace event (Pure operational audit, NO chain-of-thought text)."""
        event = AgentEvent(
            event_type=event_type,
            agent_id=agent_id,
            run_id=run_id,
            task_id=task_id,
            step_id=step_id,
            summary=summary,
            metadata=metadata or {},
        )
        return self.trace_repo.save_event(event)

    def get_trace(self, run_id: str) -> AgentTrace:
        """Alias for get_trace_for_run."""
        return self.get_trace_for_run(run_id)

    def get_trace_for_run(self, run_id: str) -> AgentTrace:
        """Retrieve complete trace container for an AgentRun."""
        return self.trace_repo.get_trace_for_run(run_id)

    def list_events_for_agent(
        self, agent_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[AgentEvent], int]:
        """List operational events for an Agent."""
        return self.trace_repo.list_events_for_agent(agent_id, limit=limit, offset=offset)
