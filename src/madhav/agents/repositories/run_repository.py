"""Repository abstractions and in-memory implementation for AgentRun entities."""

from abc import ABC, abstractmethod

from madhav.agents.domain.enums import AgentRunStatus
from madhav.agents.domain.run import AgentRun


class BaseAgentRunRepository(ABC):
    """Abstract repository interface for AgentRuns."""

    @abstractmethod
    def save(self, run: AgentRun) -> AgentRun:
        """Save or update an AgentRun instance."""
        ...

    @abstractmethod
    def get_by_id(self, run_id: str) -> AgentRun | None:
        """Retrieve an AgentRun by ID."""
        ...

    @abstractmethod
    def list_runs(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        owner_id: str | None = None,
        status: AgentRunStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentRun], int]:
        """List runs matching filter criteria."""
        ...

    @abstractmethod
    def count_active_runs_for_agent(self, agent_id: str) -> int:
        """Count active running/waiting runs for an agent."""
        ...


class MemoryAgentRunRepository(BaseAgentRunRepository):
    """In-memory implementation of AgentRun repository."""

    def __init__(self) -> None:
        self._runs: dict[str, AgentRun] = {}

    def save(self, run: AgentRun) -> AgentRun:
        self._runs[run.run_id] = run
        return run

    def get_by_id(self, run_id: str) -> AgentRun | None:
        return self._runs.get(run_id)

    def list_runs(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        owner_id: str | None = None,
        status: AgentRunStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentRun], int]:
        filtered: list[AgentRun] = []
        for run in self._runs.values():
            if agent_id and run.agent_id != agent_id:
                continue
            if task_id and run.task_id != task_id:
                continue
            if owner_id and run.owner_id != owner_id:
                continue
            if status and run.status != status:
                continue
            filtered.append(run)

        sorted_runs = sorted(filtered, key=lambda r: r.created_at, reverse=True)
        total_count = len(sorted_runs)
        return sorted_runs[offset : offset + limit], total_count

    def count_active_runs_for_agent(self, agent_id: str) -> int:
        active_states = {AgentRunStatus.RUNNING, AgentRunStatus.INITIALIZING, AgentRunStatus.READY, AgentRunStatus.WAITING}
        return sum(1 for r in self._runs.values() if r.agent_id == agent_id and r.status in active_states)


InMemoryRunRepository = MemoryAgentRunRepository
AgentRunRepository = BaseAgentRunRepository
