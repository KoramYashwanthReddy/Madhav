"""Unit tests for Agent Delegation limits, parent-child references, and cycle detection."""

import pytest

from madhav.agents.domain.agent import AgentLimits
from madhav.agents.domain.exceptions import (
    DelegationCycleError,
    DelegationLimitExceededError,
)
from madhav.agents.repositories.agent_repository import InMemoryAgentRepository
from madhav.agents.repositories.delegation_repository import InMemoryDelegationRepository
from madhav.agents.services.agent_service import AgentService
from madhav.agents.services.delegation_service import AgentDelegationService


@pytest.fixture
def agent_repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture
def delegation_repo() -> InMemoryDelegationRepository:
    return InMemoryDelegationRepository()


@pytest.fixture
def agent_service(agent_repo: InMemoryAgentRepository) -> AgentService:
    return AgentService(agent_repo)


@pytest.fixture
def delegation_service(
    delegation_repo: InMemoryDelegationRepository, agent_repo: InMemoryAgentRepository
) -> AgentDelegationService:
    return AgentDelegationService(delegation_repo=delegation_repo, agent_repo=agent_repo)


def test_valid_delegation(
    agent_service: AgentService, delegation_service: AgentDelegationService
) -> None:
    """Test valid sub-task delegation from parent agent to child agent."""
    parent = agent_service.create_agent(name="parent_agent", owner_id="user_123")
    child = agent_service.create_agent(name="child_agent", owner_id="user_123")
    agent_service.activate_agent(parent.id)
    agent_service.activate_agent(child.id)

    delegation = delegation_service.delegate_task(
        parent_agent_id=parent.id,
        child_agent_id=child.id,
        task_id="task_child_1",
        reason="Specialized processing needed",
    )

    assert delegation.parent_agent_id == parent.id
    assert delegation.child_agent_id == child.id
    assert delegation.task_id == "task_child_1"


def test_circular_delegation_prevented(
    agent_service: AgentService, delegation_service: AgentDelegationService
) -> None:
    """Test that circular delegation (A -> B -> A) raises DelegationCycleError."""
    agent_a = agent_service.create_agent(name="agent_a", owner_id="user_123")
    agent_b = agent_service.create_agent(name="agent_b", owner_id="user_123")
    agent_service.activate_agent(agent_a.id)
    agent_service.activate_agent(agent_b.id)

    # A -> B
    delegation_service.delegate_task(
        parent_agent_id=agent_a.id,
        child_agent_id=agent_b.id,
        task_id="task_1",
    )

    # B -> A (Cycle!)
    with pytest.raises(DelegationCycleError):
        delegation_service.delegate_task(
            parent_agent_id=agent_b.id,
            child_agent_id=agent_a.id,
            task_id="task_2",
        )


def test_delegation_limit_exceeded(
    agent_service: AgentService, delegation_service: AgentDelegationService
) -> None:
    """Test exceeding max_delegations limit raises DelegationLimitExceededError."""
    parent = agent_service.create_agent(
        name="limited_parent",
        limits=AgentLimits(max_delegations=2),
        owner_id="user_123",
    )
    child1 = agent_service.create_agent(name="child_1", owner_id="user_123")
    child2 = agent_service.create_agent(name="child_2", owner_id="user_123")
    child3 = agent_service.create_agent(name="child_3", owner_id="user_123")

    agent_service.activate_agent(parent.id)
    agent_service.activate_agent(child1.id)
    agent_service.activate_agent(child2.id)
    agent_service.activate_agent(child3.id)

    delegation_service.delegate_task(parent_agent_id=parent.id, child_agent_id=child1.id, task_id="t1")
    delegation_service.delegate_task(parent_agent_id=parent.id, child_agent_id=child2.id, task_id="t2")

    # Third delegation exceeds limit of 2
    with pytest.raises(DelegationLimitExceededError):
        delegation_service.delegate_task(parent_agent_id=parent.id, child_agent_id=child3.id, task_id="t3")
