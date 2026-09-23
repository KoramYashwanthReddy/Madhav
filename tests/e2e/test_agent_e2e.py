"""End-to-End acceptance tests for Module 13 Agent Engine integrated with Modules 04, 06, 11, and 12."""

import pytest

from madhav.agents.domain.agent import AgentCapability
from madhav.agents.domain.enums import AgentExecutionMode, AgentRole, AgentType
from madhav.agents.domain.run import AgentNextActionType, AgentRunStatus
from madhav.agents.providers.dev_agent import DevelopmentAgent
from madhav.agents.repositories.agent_repository import InMemoryAgentRepository
from madhav.agents.repositories.assignment_repository import InMemoryAssignmentRepository
from madhav.agents.repositories.delegation_repository import InMemoryDelegationRepository
from madhav.agents.repositories.run_repository import InMemoryRunRepository
from madhav.agents.repositories.trace_repository import InMemoryTraceRepository
from madhav.agents.services.agent_service import AgentService
from madhav.agents.services.assignment_service import AgentAssignmentService
from madhav.agents.services.boundaries import DevPermissionGateway, DevToolGateway
from madhav.agents.services.coordinator import AgentCoordinationRequest, AgentCoordinator
from madhav.agents.services.delegation_service import AgentDelegationService
from madhav.agents.services.run_service import AgentRunService
from madhav.agents.services.trace_service import AgentTraceService
from madhav.reasoning.domain.enums import PlanStatus
from madhav.reasoning.domain.plan import Plan, PlanStep
from madhav.reasoning.repositories.plan_repository import InMemoryPlanRepository
from madhav.tasks.domain.enums import TaskPriority, TaskType
from madhav.tasks.services.task_service import TaskService


@pytest.fixture
def e2e_setup():
    agent_repo = InMemoryAgentRepository()
    assignment_repo = InMemoryAssignmentRepository()
    run_repo = InMemoryRunRepository()
    trace_repo = InMemoryTraceRepository()
    delegation_repo = InMemoryDelegationRepository()
    plan_repo = InMemoryPlanRepository()

    agent_svc = AgentService(agent_repo)
    trace_svc = AgentTraceService(trace_repo)
    assign_svc = AgentAssignmentService(assignment_repo, agent_repo, trace_service=trace_svc)
    run_svc = AgentRunService(run_repo, agent_repo, trace_service=trace_svc)
    delegation_svc = AgentDelegationService(delegation_repo, agent_repo)
    task_svc = TaskService()

    coordinator = AgentCoordinator(
        agent_service=agent_svc,
        assignment_service=assign_svc,
        run_service=run_svc,
        trace_service=trace_svc,
        delegation_service=delegation_svc,
        dev_agent=DevelopmentAgent(),
        tool_gateway=DevToolGateway(),
        permission_gateway=DevPermissionGateway(),
    )

    return {
        "agent_svc": agent_svc,
        "assign_svc": assign_svc,
        "run_svc": run_svc,
        "trace_svc": trace_svc,
        "task_svc": task_svc,
        "plan_repo": plan_repo,
        "coordinator": coordinator,
    }


@pytest.mark.asyncio
async def test_agent_engine_full_e2e_acceptance_flow(e2e_setup) -> None:
    """Validate full acceptance scenario from Item 63 of Module 13 specification."""
    agent_svc = e2e_setup["agent_svc"]
    assign_svc = e2e_setup["assign_svc"]
    task_svc = e2e_setup["task_svc"]
    plan_repo = e2e_setup["plan_repo"]
    coordinator = e2e_setup["coordinator"]
    trace_svc = e2e_setup["trace_svc"]

    owner_id = "user_e2e_123"

    # 1. Create a development agent
    agent = agent_svc.create_agent(
        name="dev_coordinator",
        description="E2E Acceptance Test Coordinator",
        type=AgentType.COORDINATOR,
        role=AgentRole.COORDINATOR,
        capabilities=[AgentCapability.PLANNING, AgentCapability.TASK_COORDINATION],
        owner_id=owner_id,
    )

    # 2. Activate the agent
    activated_agent = agent_svc.activate_agent(agent.id)

    # 3. Create a Task from Module 12
    task = task_svc.create_task(
        owner_id=owner_id,
        title="Coordinate System Upgrade",
        description="Plan and execute step by step system upgrade",
        priority=TaskPriority.HIGH,
        type=TaskType.GENERAL,
    )

    # 4. Create a Plan & PlanStep from Module 11
    plan_step = PlanStep(sequence=1, title="Preparation", description="Check prerequisites")
    plan = Plan(
        title="System Upgrade Plan",
        description="E2E System Upgrade Description",
        steps=[plan_step],
        status=PlanStatus.ACTIVE,
        owner_id=owner_id,
    )
    await plan_repo.save(plan)

    # 5. Create an AgentAssignment and Accept it
    assignment = assign_svc.assign_task(
        agent_id=activated_agent.id,
        task_id=task.id,
        plan_id=plan.plan_id,
        reason="Assigned via E2E orchestration",
    )
    assign_svc.accept_assignment(assignment.assignment_id)

    # 6. Coordinate execution using AgentCoordinator
    coord_req = AgentCoordinationRequest(
        owner_id=owner_id,
        agent_id=activated_agent.id,
        task_id=task.id,
        plan_id=plan.plan_id,
        plan_step_id=plan_step.step_id,
        objective="Prepare system for upgrade",
        execution_mode=AgentExecutionMode.DRY_RUN,
    )

    response = coordinator.coordinate(coord_req)

    # 7. Verify structured response and state changes
    assert response.status == AgentRunStatus.COMPLETED
    assert response.agent_id == activated_agent.id
    assert response.task_id == task.id
    assert response.result is not None
    assert response.result.summary != ""
    assert response.next_action == AgentNextActionType.COMPLETE

    # 8. Verify operational traces were logged cleanly
    trace = trace_svc.get_trace(response.run_id)
    assert len(trace.events) > 0
    event_types = [e.event_type.value for e in trace.events]
    assert "RUN_CREATED" in event_types
    assert "RUN_STARTED" in event_types
    assert "RUN_COMPLETED" in event_types
