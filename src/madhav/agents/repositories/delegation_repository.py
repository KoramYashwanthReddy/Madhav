"""Repository abstractions and in-memory implementation for AgentDelegation entities."""

from abc import ABC, abstractmethod

from madhav.agents.domain.delegation import AgentDelegation


class BaseAgentDelegationRepository(ABC):
    """Abstract repository interface for AgentDelegations."""

    @abstractmethod
    def save(self, delegation: AgentDelegation) -> AgentDelegation:
        """Save a delegation relationship record."""
        ...

    @abstractmethod
    def get_by_id(self, delegation_id: str) -> AgentDelegation | None:
        """Retrieve a delegation by ID."""
        ...

    @abstractmethod
    def list_delegations_for_run(self, parent_run_id: str) -> list[AgentDelegation]:
        """List outgoing delegations initiated by a parent run."""
        ...

    @abstractmethod
    def count_delegations_for_run(self, parent_run_id: str) -> int:
        """Count total sub-delegations initiated by a parent run."""
        ...


class MemoryAgentDelegationRepository(BaseAgentDelegationRepository):
    """In-memory implementation of AgentDelegation repository."""

    def __init__(self) -> None:
        self._delegations: dict[str, AgentDelegation] = {}

    def save(self, delegation: AgentDelegation) -> AgentDelegation:
        self._delegations[delegation.delegation_id] = delegation
        return delegation

    def get_by_id(self, delegation_id: str) -> AgentDelegation | None:
        return self._delegations.get(delegation_id)

    def list_delegations_for_run(self, parent_run_id: str) -> list[AgentDelegation]:
        return [d for d in self._delegations.values() if d.parent_run_id == parent_run_id]

    def count_delegations_for_run(self, parent_run_id: str) -> int:
        return sum(1 for d in self._delegations.values() if d.parent_run_id == parent_run_id)


InMemoryDelegationRepository = MemoryAgentDelegationRepository
AgentDelegationRepository = BaseAgentDelegationRepository
