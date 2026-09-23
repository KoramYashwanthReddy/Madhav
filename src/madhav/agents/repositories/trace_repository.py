"""Repository abstractions and in-memory implementation for AgentTrace and operational events."""

from abc import ABC, abstractmethod

from madhav.agents.domain.trace import AgentEvent, AgentTrace


class BaseAgentTraceRepository(ABC):
    """Abstract repository interface for AgentEvent and AgentTrace persistence."""

    @abstractmethod
    def save_event(self, event: AgentEvent) -> AgentEvent:
        """Record an operational trace event."""
        ...

    @abstractmethod
    def get_trace_for_run(self, run_id: str) -> AgentTrace:
        """Retrieve complete trace audit container for an AgentRun."""
        ...

    @abstractmethod
    def list_events_for_agent(
        self, agent_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[AgentEvent], int]:
        """List trace events for an agent."""
        ...


class MemoryAgentTraceRepository(BaseAgentTraceRepository):
    """In-memory implementation of AgentTrace repository."""

    def __init__(self) -> None:
        self._events_by_run: dict[str, list[AgentEvent]] = {}
        self._events_by_agent: dict[str, list[AgentEvent]] = {}

    def save_event(self, event: AgentEvent) -> AgentEvent:
        if event.run_id:
            if event.run_id not in self._events_by_run:
                self._events_by_run[event.run_id] = []
            self._events_by_run[event.run_id].append(event)

        if event.agent_id not in self._events_by_agent:
            self._events_by_agent[event.agent_id] = []
        self._events_by_agent[event.agent_id].append(event)

        return event

    def get_trace_for_run(self, run_id: str) -> AgentTrace:
        events = self._events_by_run.get(run_id, [])
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        agent_id = sorted_events[0].agent_id if sorted_events else "unknown"
        return AgentTrace(run_id=run_id, agent_id=agent_id, events=sorted_events)

    def list_events_for_agent(
        self, agent_id: str, limit: int = 100, offset: int = 0
    ) -> tuple[list[AgentEvent], int]:
        events = self._events_by_agent.get(agent_id, [])
        sorted_events = sorted(events, key=lambda e: e.timestamp, reverse=True)
        total_count = len(sorted_events)
        return sorted_events[offset : offset + limit], total_count


InMemoryTraceRepository = MemoryAgentTraceRepository
AgentTraceRepository = BaseAgentTraceRepository
