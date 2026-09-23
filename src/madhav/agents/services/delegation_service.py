"""Agent delegation service managing inter-agent delegations and loop detection."""

from datetime import datetime
from typing import Any

from madhav.agents.domain.agent import Agent
from madhav.agents.domain.delegation import AgentDelegation
from madhav.agents.domain.enums import DelegationStatus
from madhav.agents.domain.exceptions import (
    AgentNotFoundError,
    DelegationCycleError,
    DelegationLimitExceededError,
)
from madhav.agents.repositories.agent_repository import BaseAgentRepository, MemoryAgentRepository
from madhav.agents.repositories.delegation_repository import (
    BaseAgentDelegationRepository,
    MemoryAgentDelegationRepository,
)


class AgentDelegationService:
    """Service managing inter-agent delegation links and structural limits."""

    def __init__(
        self,
        delegation_repo: BaseAgentDelegationRepository | None = None,
        agent_repo: BaseAgentRepository | None = None,
    ) -> None:
        self.delegation_repo = delegation_repo or MemoryAgentDelegationRepository()
        self.agent_repo = agent_repo or MemoryAgentRepository()

    def delegate_task(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        task_id: str,
        parent_run_id: str | None = None,
        reason: str = "Subtask delegation",
        metadata: dict[str, Any] | None = None,
    ) -> AgentDelegation:
        """Create and validate a new sub-delegation link by agent IDs."""
        parent_agent = self.agent_repo.get_by_id(parent_agent_id)
        if not parent_agent:
            raise AgentNotFoundError(f"Parent agent {parent_agent_id} not found")
        child_agent = self.agent_repo.get_by_id(child_agent_id)
        if not child_agent:
            raise AgentNotFoundError(f"Child agent {child_agent_id} not found")

        # Check self-delegation or cycle
        if parent_agent_id == child_agent_id:
            raise DelegationCycleError(cycle=[parent_agent_id, child_agent_id])

        # Enforce cycle prevention in active delegation chain
        parent_delegations = self.get_delegations_for_agent(parent_agent_id)
        for d in parent_delegations:
            if d.parent_agent_id == child_agent_id:
                raise DelegationCycleError(cycle=[parent_agent_id, child_agent_id, parent_agent_id])

        # Enforce max delegations count limit
        if parent_run_id:
            existing_count = self.delegation_repo.count_delegations_for_run(parent_run_id)
            if existing_count >= parent_agent.limits.max_delegations:
                raise DelegationLimitExceededError(
                    f"Parent run {parent_run_id} reached max delegation limit {parent_agent.limits.max_delegations}"
                )
        else:
            existing_count = len([d for d in parent_delegations if d.parent_agent_id == parent_agent_id])
            if existing_count >= parent_agent.limits.max_delegations:
                raise DelegationLimitExceededError(
                    f"Parent agent {parent_agent_id} reached max delegation limit {parent_agent.limits.max_delegations}"
                )

        delegation = AgentDelegation(
            parent_agent_id=parent_agent_id,
            child_agent_id=child_agent_id,
            task_id=task_id,
            parent_run_id=parent_run_id,
            reason=reason,
            status=DelegationStatus.REQUESTED,
            metadata=metadata or {},
        )
        return self.delegation_repo.save(delegation)

    def create_delegation(
        self,
        parent_agent: Agent,
        child_agent_id: str,
        parent_run_id: str,
        task_id: str | None = None,
        reason: str = "Subtask delegation",
        metadata: dict[str, Any] | None = None,
    ) -> AgentDelegation:
        """Create and validate a new sub-delegation link."""
        return self.delegate_task(
            parent_agent_id=parent_agent.id,
            child_agent_id=child_agent_id,
            task_id=task_id or "task_default",
            parent_run_id=parent_run_id,
            reason=reason,
            metadata=metadata,
        )

    def get_delegations_for_agent(self, agent_id: str) -> list[AgentDelegation]:
        """List all delegations involving an agent as parent or child."""
        if hasattr(self.delegation_repo, "_delegations"):
            return [
                d
                for d in self.delegation_repo._delegations.values()
                if d.parent_agent_id == agent_id or d.child_agent_id == agent_id
            ]
        return []

    def update_delegation_status(
        self,
        delegation_id: str,
        status: DelegationStatus,
        child_run_id: str | None = None,
    ) -> AgentDelegation:
        """Update delegation status."""
        delegation = self.delegation_repo.get_by_id(delegation_id)
        if not delegation:
            raise DelegationLimitExceededError(f"Delegation record '{delegation_id}' not found.")

        updated_dict = delegation.model_dump()
        updated_dict["status"] = status
        if child_run_id:
            updated_dict["child_run_id"] = child_run_id
        if status in (DelegationStatus.COMPLETED, DelegationStatus.FAILED, DelegationStatus.CANCELLED):
            updated_dict["completed_at"] = datetime.utcnow()

        new_delegation = AgentDelegation(**updated_dict)
        return self.delegation_repo.save(new_delegation)
