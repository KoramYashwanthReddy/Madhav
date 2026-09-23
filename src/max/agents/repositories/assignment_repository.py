"""Repository abstractions and in-memory implementation for AgentAssignment entities."""

from abc import ABC, abstractmethod

from max.agents.domain.assignment import AgentAssignment
from max.agents.domain.enums import AgentAssignmentStatus


class BaseAgentAssignmentRepository(ABC):
    """Abstract repository interface for AgentAssignments."""

    @abstractmethod
    def save(self, assignment: AgentAssignment) -> AgentAssignment:
        """Save or update an assignment record."""
        ...

    @abstractmethod
    def get_by_id(self, assignment_id: str) -> AgentAssignment | None:
        """Retrieve an assignment by ID."""
        ...

    @abstractmethod
    def get_by_agent_and_task(self, agent_id: str, task_id: str) -> AgentAssignment | None:
        """Retrieve active assignment link for agent and task."""
        ...

    @abstractmethod
    def list_assignments(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        owner_id: str | None = None,
        status: AgentAssignmentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentAssignment], int]:
        """List assignments matching criteria."""
        ...


class MemoryAgentAssignmentRepository(BaseAgentAssignmentRepository):
    """In-memory implementation of AgentAssignment repository."""

    def __init__(self) -> None:
        self._assignments: dict[str, AgentAssignment] = {}

    def save(self, assignment: AgentAssignment) -> AgentAssignment:
        self._assignments[assignment.assignment_id] = assignment
        return assignment

    def get_by_id(self, assignment_id: str) -> AgentAssignment | None:
        return self._assignments.get(assignment_id)

    def get_by_agent_and_task(self, agent_id: str, task_id: str) -> AgentAssignment | None:
        for asgn in self._assignments.values():
            if asgn.agent_id == agent_id and asgn.task_id == task_id:
                return asgn
        return None

    def list_assignments(
        self,
        agent_id: str | None = None,
        task_id: str | None = None,
        owner_id: str | None = None,
        status: AgentAssignmentStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AgentAssignment], int]:
        filtered: list[AgentAssignment] = []
        for asgn in self._assignments.values():
            if agent_id and asgn.agent_id != agent_id:
                continue
            if task_id and asgn.task_id != task_id:
                continue
            if owner_id and asgn.owner_id != owner_id:
                continue
            if status and asgn.status != status:
                continue
            filtered.append(asgn)

        sorted_asgns = sorted(filtered, key=lambda a: a.assigned_at, reverse=True)
        total_count = len(sorted_asgns)
        return sorted_asgns[offset : offset + limit], total_count


InMemoryAssignmentRepository = MemoryAgentAssignmentRepository
AgentAssignmentRepository = BaseAgentAssignmentRepository
