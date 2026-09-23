"""Unit tests for Module 13 Agent Engine Coordinator and boundary enforcement."""

import pytest

from max.agents.domain.agent import AgentCapability
from max.agents.domain.enums import AgentExecutionMode, AgentRole, AgentType
from max.agents.domain.exceptions import AgentInactiveError
from max.agents.domain.run import AgentNextActionType, AgentRunStatus
from max.agents.providers.dev_agent import DevelopmentAgent
from max.agents.repositories.agent_repository import InMemoryAgentRepository
from max.agents.repositories.assignment_repository import InMemoryAssignmentRepository
from max.agents.repositories.delegation_repository import InMemoryDelegationRepository
from max.agents.repositories.run_repository import InMemoryRunRepository
from max.agents.repositories.trace_repository import InMemoryTraceRepository
from max.agents.services.agent_service import AgentService
from max.agents.services.assignment_service import AgentAssignmentService
from max.agents.services.boundaries import DevPermissionGateway, DevToolGateway
from max.agents.services.coordinator import AgentCoordinationRequest, AgentCoordinator
from max.agents.services.delegation_service import AgentDelegationService
from max.agents.services.run_service import AgentRunService
from max.agents.services.trace_service import AgentTraceService


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
def trace_repo() -> InMemoryTraceRepository:
    return InMemoryTraceRepository()


@pytest.fixture
def delegation_repo() -> InMemoryDelegationRepository:
    return InMemoryDelegationRepository()


@pytest.fixture
def coordinator(
    agent_repo: InMemoryAgentRepository,
    assignment_repo: InMemoryAssignmentRepository,
    run_repo: InMemoryRunRepository,
    trace_repo: InMemoryTraceRepository,
    delegation_repo: InMemoryDelegationRepository,
) -> AgentCoordinator:
    agent_svc = AgentService(agent_repo)
    assign_svc = AgentAssignmentService(assignment_repo, agent_repo)
    run_svc = AgentRunService(run_repo, agent_repo)
    trace_svc = AgentTraceService(trace_repo)
    delegation_svc = AgentDelegationService(delegation_repo, agent_repo)

    return AgentCoordinator(
        agent_service=agent_svc,
        assignment_service=assign_svc,
        run_service=run_svc,
        trace_service=trace_svc,
        delegation_service=delegation_svc,
        dev_agent=DevelopmentAgent(),
        tool_gateway=DevToolGateway(),
        permission_gateway=DevPermissionGateway(),
    )


def test_coordinator_acceptance_scenario(coordinator: AgentCoordinator) -> None:
    """Test full coordinator lifecycle completing a task deterministically (NextAction=COMPLETE)."""
    agent = coordinator.agent_service.create_agent(
        name="coord_agent",
        type=AgentType.COORDINATOR,
        role=AgentRole.COORDINATOR,
        capabilities=[AgentCapability.TASK_COORDINATION, AgentCapability.PLANNING],
        owner_id="user_123",
    )
    coordinator.agent_service.activate_agent(agent.id)

    request = AgentCoordinationRequest(
        owner_id="user_123",
        agent_id=agent.id,
        task_id="task_001",
        objective="Analyze dataset and report findings",
        execution_mode=AgentExecutionMode.DRY_RUN,
    )

    response = coordinator.coordinate(request)

    assert response.status == AgentRunStatus.COMPLETED
    assert response.agent_id == agent.id
    assert response.task_id == "task_001"
    assert response.result is not None
    assert response.result.summary != ""
    assert response.next_action == AgentNextActionType.COMPLETE


def test_coordinator_tool_boundary_scenario(coordinator: AgentCoordinator) -> None:
    """Test tool boundary enforcement: NextAction=REQUEST_TOOL creates ToolRequestIntent with status NOT_IMPLEMENTED and DOES NOT execute tools."""
    agent = coordinator.agent_service.create_agent(
        name="tool_requesting_agent",
        type=AgentType.EXECUTOR,
        capabilities=[AgentCapability.TASK_COORDINATION],
        owner_id="user_123",
    )
    coordinator.agent_service.activate_agent(agent.id)

    request = AgentCoordinationRequest(
        owner_id="user_123",
        agent_id=agent.id,
        task_id="task_tool_req",
        objective="Request tool execution for calculation",
        metadata={"simulate_next_action": "REQUEST_TOOL"},
    )

    response = coordinator.coordinate(request)

    assert response.next_action == AgentNextActionType.REQUEST_TOOL
    assert len(response.tool_requests) == 1
    assert response.tool_requests[0].status == "NOT_IMPLEMENTED"


def test_coordinator_permission_boundary_scenario(coordinator: AgentCoordinator) -> None:
    """Test permission boundary enforcement: NextAction=REQUEST_PERMISSION creates PermissionRequestIntent with status NOT_IMPLEMENTED and DOES NOT grant permissions."""
    agent = coordinator.agent_service.create_agent(
        name="perm_requesting_agent",
        type=AgentType.EXECUTOR,
        capabilities=[AgentCapability.TASK_COORDINATION],
        owner_id="user_123",
    )
    coordinator.agent_service.activate_agent(agent.id)

    request = AgentCoordinationRequest(
        owner_id="user_123",
        agent_id=agent.id,
        task_id="task_perm_req",
        objective="Request permission for restricted access",
        metadata={"simulate_next_action": "REQUEST_PERMISSION"},
    )

    response = coordinator.coordinate(request)

    assert response.next_action == AgentNextActionType.REQUEST_PERMISSION
    assert len(response.permission_requests) == 1
    assert response.permission_requests[0].status == "NOT_IMPLEMENTED"


def test_coordinator_inactive_agent_rejected(coordinator: AgentCoordinator) -> None:
    """Verify that coordinating with an inactive or non-existent agent raises appropriate errors."""
    agent = coordinator.agent_service.create_agent(
        name="inactive_agent", owner_id="user_123"
    )
    # Status is CREATED (not active)

    request = AgentCoordinationRequest(
        owner_id="user_123",
        agent_id=agent.id,
        task_id="task_1",
        objective="Run task",
    )

    with pytest.raises(AgentInactiveError):
        coordinator.coordinate(request)
