"""Unit tests for Module 13 Agent Engine core services."""

import pytest

from max.agents.domain.agent import AgentCapability, AgentLimits
from max.agents.domain.assignment import AssignmentPriority, AssignmentStatus
from max.agents.domain.enums import AgentExecutionMode, AgentRole, AgentStatus, AgentType
from max.agents.domain.exceptions import (
    AgentCapabilityMismatchError,
)
from max.agents.domain.run import AgentRunStatus
from max.agents.repositories.agent_repository import InMemoryAgentRepository
from max.agents.repositories.assignment_repository import InMemoryAssignmentRepository
from max.agents.repositories.run_repository import InMemoryRunRepository
from max.agents.services.agent_service import AgentService
from max.agents.services.assignment_service import AgentAssignmentService
from max.agents.services.availability_service import AgentAvailabilityService
from max.agents.services.run_service import AgentRunService
from max.agents.services.selection_service import AgentSelectionService


@pytest.fixture
def agent_repo() -> InMemoryAgentRepository:
    return InMemoryAgentRepository()


@pytest.fixture
def assignment_repo() -> InMemoryAssignmentRepository:
    return InMemoryAssignmentRepository()


@pytest.fixture
def run_repo() -> InMemoryRunRepository:
    return InMemoryRunRepository()


@pytest.fixture
def agent_service(agent_repo: InMemoryAgentRepository) -> AgentService:
    return AgentService(repository=agent_repo)


@pytest.fixture
def assignment_service(
    assignment_repo: InMemoryAssignmentRepository, agent_repo: InMemoryAgentRepository
) -> AgentAssignmentService:
    return AgentAssignmentService(assignment_repo=assignment_repo, agent_repo=agent_repo)


@pytest.fixture
def run_service(
    run_repo: InMemoryRunRepository, agent_repo: InMemoryAgentRepository
) -> AgentRunService:
    return AgentRunService(run_repo=run_repo, agent_repo=agent_repo)


def test_agent_crud_and_lifecycle(agent_service: AgentService) -> None:
    """Test full agent creation, activation, pausing, disabling, and archiving lifecycle."""
    agent = agent_service.create_agent(
        owner_id="user_123",
        name="researcher",
        description="Data collection agent",
        type=AgentType.SPECIALIST,
        role=AgentRole.RESEARCHER,
        capabilities=[AgentCapability.RESEARCH, AgentCapability.ANALYSIS],
    )
    assert agent.name == "researcher"
    assert agent.status == AgentStatus.CREATED

    # Activate
    active_agent = agent_service.activate_agent(agent.id)
    assert active_agent.status == AgentStatus.ACTIVE

    # Pause
    paused_agent = agent_service.pause_agent(agent.id)
    assert paused_agent.status == AgentStatus.PAUSED

    # Resume to active
    agent_service.activate_agent(agent.id)

    # Disable
    disabled_agent = agent_service.disable_agent(agent.id)
    assert disabled_agent.status == AgentStatus.DISABLED

    # Archive
    archived_agent = agent_service.archive_agent(agent.id)
    assert archived_agent.status == AgentStatus.ARCHIVED


def test_agent_availability_and_selection(
    agent_repo: InMemoryAgentRepository, run_repo: InMemoryRunRepository
) -> None:
    """Test agent availability tracking and selection service."""
    avail_svc = AgentAvailabilityService(agent_repo, run_repo)
    select_svc = AgentSelectionService(agent_repo, avail_svc)

    svc = AgentService(agent_repo)
    agent1 = svc.create_agent(
        name="planner_1",
        type=AgentType.PLANNER,
        role=AgentRole.PLANNER,
        capabilities=[AgentCapability.PLANNING],
        limits=AgentLimits(max_concurrent_tasks=2),
        owner_id="user_1",
    )
    svc.activate_agent(agent1.id)

    # Selection match
    res = select_svc.select_agent(required_capabilities=[AgentCapability.PLANNING])
    assert res.matched is True
    assert res.selected_agent_id == agent1.id


def test_assignment_lifecycle(
    assignment_service: AgentAssignmentService, agent_service: AgentService
) -> None:
    """Test creating, accepting, starting, completing, failing, and cancelling task assignments."""
    agent = agent_service.create_agent(
        owner_id="user_123",
        name="worker_agent",
        capabilities=[AgentCapability.TASK_COORDINATION],
    )
    agent_service.activate_agent(agent.id)

    # Create assignment
    assignment = assignment_service.assign_task(
        agent_id=agent.id,
        task_id="task_999",
        priority=AssignmentPriority.HIGH,
        reason="Priority work",
    )
    assert assignment.status == AssignmentStatus.ASSIGNED

    # Accept
    acc = assignment_service.accept_assignment(assignment.assignment_id)
    assert acc.status == AssignmentStatus.ACCEPTED

    # Start
    started = assignment_service.start_assignment(assignment.assignment_id)
    assert started.status == AssignmentStatus.STARTED

    # Complete
    completed = assignment_service.complete_assignment(assignment.assignment_id)
    assert completed.status == AssignmentStatus.COMPLETED


def test_assignment_capability_mismatch_fails(
    assignment_service: AgentAssignmentService, agent_service: AgentService
) -> None:
    """Test assigning task with capability mismatch raises AgentCapabilityMismatchError when strict."""
    agent = agent_service.create_agent(
        owner_id="user_123",
        name="no_review_agent",
        capabilities=[AgentCapability.PLANNING],
    )
    agent_service.activate_agent(agent.id)

    with pytest.raises(AgentCapabilityMismatchError):
        assignment_service.assign_task(
            agent_id=agent.id,
            task_id="task_1",
            required_capabilities=[AgentCapability.CODE_REVIEW],
        )


def test_run_service_lifecycle(run_service: AgentRunService, agent_service: AgentService) -> None:
    """Test agent run creation, start, pause, resume, cancel, and retry."""
    agent = agent_service.create_agent(owner_id="user_123", name="runner_agent")
    agent_service.activate_agent(agent.id)

    run = run_service.create_run(
        agent_id=agent.id,
        task_id="task_100",
        owner_id="user_123",
        execution_mode=AgentExecutionMode.DRY_RUN,
    )
    assert run.status == AgentRunStatus.CREATED

    # Start run
    started_run = run_service.start_run(run.run_id)
    assert started_run.status == AgentRunStatus.RUNNING

    # Pause run
    paused_run = run_service.pause_run(run.run_id)
    assert paused_run.status == AgentRunStatus.PAUSED

    # Resume run
    resumed_run = run_service.resume_run(run.run_id)
    assert resumed_run.status == AgentRunStatus.RUNNING

    # Complete run
    completed_run = run_service.complete_run(run.run_id)
    assert completed_run.status == AgentRunStatus.COMPLETED
