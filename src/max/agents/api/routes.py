"""FastAPI REST API routes for Module 13 Agent Engine."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from max.agents.domain.exceptions import (
    AgentAssignmentNotFoundError,
    AgentCapabilityMismatchError,
    AgentError,
    AgentExecutionBoundaryError,
    AgentInactiveError,
    AgentLimitExceededError,
    AgentNotFoundError,
    AgentRunNotFoundError,
    AgentUnavailableError,
    DelegationCycleError,
    DelegationLimitExceededError,
    InvalidAgentStateTransitionError,
    InvalidRunStateTransitionError,
)
from max.agents.schemas.requests import (
    CreateAgentRequest,
    CreateAssignmentRequest,
    CreateDelegationRequest,
    CreateRunRequest,
    SelectAgentRequest,
    UpdateAgentRequest,
)
from max.agents.schemas.responses import (
    AgentAssignmentResponse,
    AgentAvailabilityResponse,
    AgentCapabilitiesResponse,
    AgentDelegationResponse,
    AgentResponse,
    AgentRunResponse,
    AgentSelectionResponse,
    AgentTraceResponse,
)
from max.agents.services.agent_service import AgentService
from max.agents.services.assignment_service import AgentAssignmentService
from max.agents.services.availability_service import AgentAvailabilityService
from max.agents.services.delegation_service import AgentDelegationService
from max.agents.services.run_service import AgentRunService
from max.agents.services.selection_service import AgentSelectionService
from max.agents.services.trace_service import AgentTraceService

router = APIRouter(prefix="/agents", tags=["Agent Engine"])

_agent_service: AgentService | None = None
_assignment_service: AgentAssignmentService | None = None
_run_service: AgentRunService | None = None
_delegation_service: AgentDelegationService | None = None
_selection_service: AgentSelectionService | None = None
_availability_service: AgentAvailabilityService | None = None
_trace_service: AgentTraceService | None = None


def get_agent_service() -> AgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


def get_assignment_service() -> AgentAssignmentService:
    global _assignment_service
    if _assignment_service is None:
        agent_svc = get_agent_service()
        _assignment_service = AgentAssignmentService(agent_repo=agent_svc.repository)
    return _assignment_service


def get_run_service() -> AgentRunService:
    global _run_service
    if _run_service is None:
        agent_svc = get_agent_service()
        _run_service = AgentRunService(agent_repo=agent_svc.repository)
    return _run_service


def get_delegation_service() -> AgentDelegationService:
    global _delegation_service
    if _delegation_service is None:
        agent_svc = get_agent_service()
        _delegation_service = AgentDelegationService(agent_repo=agent_svc.repository)
    return _delegation_service


def get_selection_service() -> AgentSelectionService:
    global _selection_service
    if _selection_service is None:
        agent_svc = get_agent_service()
        avail_svc = get_availability_service()
        _selection_service = AgentSelectionService(agent_svc.repository, avail_svc)
    return _selection_service


def get_availability_service() -> AgentAvailabilityService:
    global _availability_service
    if _availability_service is None:
        agent_svc = get_agent_service()
        run_svc = get_run_service()
        _availability_service = AgentAvailabilityService(agent_svc.repository, run_svc.repository)
    return _availability_service


def get_trace_service() -> AgentTraceService:
    global _trace_service
    if _trace_service is None:
        _trace_service = AgentTraceService()
    return _trace_service


def _handle_agent_error(e: AgentError) -> None:
    if isinstance(e, (AgentNotFoundError, AgentAssignmentNotFoundError, AgentRunNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(
        e,
        (
            InvalidAgentStateTransitionError,
            InvalidRunStateTransitionError,
            DelegationCycleError,
        ),
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    elif isinstance(
        e,
        (
            AgentCapabilityMismatchError,
            AgentLimitExceededError,
            DelegationLimitExceededError,
            AgentInactiveError,
            AgentUnavailableError,
            AgentExecutionBoundaryError,
        ),
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _to_agent_response(agent: Any) -> AgentResponse:
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        type=agent.type,
        role=agent.role,
        status=agent.status,
        capabilities=agent.capabilities,
        configuration=agent.configuration,
        limits=agent.limits,
        owner_id=agent.owner_id,
        metadata=agent.metadata,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
    )


def _to_assignment_response(assignment: Any) -> AgentAssignmentResponse:
    return AgentAssignmentResponse(
        assignment_id=assignment.assignment_id,
        agent_id=assignment.agent_id,
        task_id=assignment.task_id,
        plan_id=assignment.plan_id,
        status=assignment.status,
        priority=assignment.priority,
        reason=assignment.reason,
        metadata=assignment.metadata,
        assigned_at=assignment.assigned_at,
        updated_at=assignment.updated_at,
    )


def _to_run_response(run: Any) -> AgentRunResponse:
    return AgentRunResponse(
        run_id=run.run_id,
        agent_id=run.agent_id,
        task_id=run.task_id,
        plan_id=run.plan_id,
        conversation_id=run.conversation_id,
        owner_id=run.owner_id,
        status=run.status,
        execution_mode=run.execution_mode,
        retry_count=run.retry_count,
        client_request_id=run.client_request_id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        failure=run.failure,
        result=run.result,
        next_action=run.next_action,
        metadata=run.metadata,
        created_at=run.created_at,
    )


# ==================================================
# AGENT MANAGEMENT ENDPOINTS
# ==================================================


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def create_agent(
    req: CreateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Create a new logical agent definition."""
    try:
        agent = service.create_agent(
            name=req.name,
            description=req.description,
            type=req.type,
            role=req.role,
            capabilities=req.capabilities,
            configuration=req.configuration,
            limits=req.limits,
            owner_id=req.owner_id,
            metadata=req.metadata,
        )
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("", response_model=list[AgentResponse])
def list_agents(
    owner_id: str | None = Query(default=None, description="Filter by owner ID"),
    page: int = Query(default=1, ge=1, description="Page index"),
    page_size: int = Query(default=50, ge=1, le=100, description="Page size"),
    service: AgentService = Depends(get_agent_service),
) -> list[AgentResponse]:
    """List registered agents with optional owner filter and pagination."""
    offset = (page - 1) * page_size
    agents_list, _ = service.list_agents(owner_id=owner_id, limit=page_size, offset=offset)
    return [_to_agent_response(a) for a in agents_list]


@router.post("/select", response_model=AgentSelectionResponse)
def select_agent(
    req: SelectAgentRequest,
    service: AgentSelectionService = Depends(get_selection_service),
) -> AgentSelectionResponse:
    """Select the best matching agent for a task deterministically."""
    result = service.select_agent(
        required_capabilities=req.required_capabilities,
        task_type=req.task_type,
        preferred_role=req.preferred_role,
        preferred_type=req.preferred_type,
    )
    return AgentSelectionResponse(
        selected_agent_id=result.selected_agent_id,
        selected_agent_name=result.selected_agent_name,
        matched=result.matched,
        reason=result.reason,
        evaluated_agent_count=result.evaluated_agent_count,
    )


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Retrieve agent by ID."""
    try:
        agent = service.get_agent(agent_id)
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.patch("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    req: UpdateAgentRequest,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Update properties of an existing agent."""
    try:
        agent = service.update_agent(
            agent_id=agent_id,
            name=req.name,
            description=req.description,
            type=req.type,
            role=req.role,
            capabilities=req.capabilities,
            configuration=req.configuration,
            limits=req.limits,
            metadata=req.metadata,
        )
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> None:
    """Archive and delete agent."""
    try:
        service.archive_agent(agent_id)
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# AGENT LIFECYCLE ENDPOINTS
# ==================================================


@router.post("/{agent_id}/activate", response_model=AgentResponse)
def activate_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Transition agent status to ACTIVE."""
    try:
        agent = service.activate_agent(agent_id)
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/pause", response_model=AgentResponse)
def pause_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Transition agent status to PAUSED."""
    try:
        agent = service.pause_agent(agent_id)
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/disable", response_model=AgentResponse)
def disable_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Transition agent status to DISABLED."""
    try:
        agent = service.disable_agent(agent_id)
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/archive", response_model=AgentResponse)
def archive_agent(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Transition agent status to ARCHIVED."""
    try:
        agent = service.archive_agent(agent_id)
        return _to_agent_response(agent)
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# CAPABILITIES AND AVAILABILITY ENDPOINTS
# ==================================================


@router.get("/{agent_id}/capabilities", response_model=AgentCapabilitiesResponse)
def get_agent_capabilities(
    agent_id: str,
    service: AgentService = Depends(get_agent_service),
) -> AgentCapabilitiesResponse:
    """Get claims of agent capabilities."""
    try:
        agent = service.get_agent(agent_id)
        return AgentCapabilitiesResponse(
            agent_id=agent.id,
            capabilities=agent.capabilities,
        )
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("/{agent_id}/availability", response_model=AgentAvailabilityResponse)
def get_agent_availability(
    agent_id: str,
    service: AgentAvailabilityService = Depends(get_availability_service),
) -> AgentAvailabilityResponse:
    """Get current runtime capacity and availability status."""
    try:
        availability = service.check_availability(agent_id)
        return AgentAvailabilityResponse(
            agent_id=availability.agent_id,
            is_available=availability.is_available,
            active_runs_count=availability.active_runs_count,
            max_concurrent_tasks=availability.max_concurrent_tasks,
            status=availability.status,
        )
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# ASSIGNMENTS ENDPOINTS
# ==================================================


@router.post(
    "/{agent_id}/assignments",
    response_model=AgentAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_task(
    agent_id: str,
    req: CreateAssignmentRequest,
    service: AgentAssignmentService = Depends(get_assignment_service),
) -> AgentAssignmentResponse:
    """Assign a task to an agent."""
    try:
        assignment = service.assign_task(
            agent_id=agent_id,
            task_id=req.task_id,
            plan_id=req.plan_id,
            priority=req.priority,
            reason=req.reason,
            metadata=req.metadata,
        )
        return _to_assignment_response(assignment)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("/{agent_id}/assignments", response_model=list[AgentAssignmentResponse])
def list_assignments(
    agent_id: str,
    service: AgentAssignmentService = Depends(get_assignment_service),
) -> list[AgentAssignmentResponse]:
    """List all task assignments for an agent."""
    try:
        assignments = service.list_assignments_for_agent(agent_id)
        return [_to_assignment_response(a) for a in assignments]
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# RUNS ENDPOINTS
# ==================================================


@router.post(
    "/{agent_id}/runs", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED
)
def create_run(
    agent_id: str,
    req: CreateRunRequest,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Create a new agent execution run."""
    try:
        run = service.create_run(
            agent_id=agent_id,
            task_id=req.task_id,
            plan_id=req.plan_id,
            conversation_id=req.conversation_id,
            owner_id=req.owner_id,
            execution_mode=req.execution_mode,
            client_request_id=req.client_request_id,
            metadata=req.metadata,
        )
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("/{agent_id}/runs", response_model=list[AgentRunResponse])
def list_runs(
    agent_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> list[AgentRunResponse]:
    """List all execution runs for an agent."""
    try:
        runs = service.list_runs_for_agent(agent_id)
        return [_to_run_response(r) for r in runs]
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("/{agent_id}/runs/{run_id}", response_model=AgentRunResponse)
def get_run(
    agent_id: str,
    run_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Retrieve details of a specific agent run."""
    try:
        run = service.get_run(run_id)
        if run.agent_id != agent_id:
            raise AgentRunNotFoundError(f"Run {run_id} does not belong to agent {agent_id}")
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/runs/{run_id}/start", response_model=AgentRunResponse)
def start_run(
    agent_id: str,
    run_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Start execution lifecycle of an initialized run."""
    try:
        run = service.start_run(run_id)
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/runs/{run_id}/pause", response_model=AgentRunResponse)
def pause_run(
    agent_id: str,
    run_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Pause a running agent run."""
    try:
        run = service.pause_run(run_id)
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/runs/{run_id}/resume", response_model=AgentRunResponse)
def resume_run(
    agent_id: str,
    run_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Resume a paused agent run."""
    try:
        run = service.resume_run(run_id)
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/runs/{run_id}/cancel", response_model=AgentRunResponse)
def cancel_run(
    agent_id: str,
    run_id: str,
    reason: str = Query(default="Cancelled by API request", description="Reason for cancellation"),
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Cancel an active agent run."""
    try:
        run = service.cancel_run(run_id, reason=reason)
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.post("/{agent_id}/runs/{run_id}/retry", response_model=AgentRunResponse)
def retry_run(
    agent_id: str,
    run_id: str,
    service: AgentRunService = Depends(get_run_service),
) -> AgentRunResponse:
    """Retry a failed or timed out agent run."""
    try:
        run = service.retry_run(run_id)
        return _to_run_response(run)
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# TRACE ENDPOINTS
# ==================================================


@router.get("/{agent_id}/runs/{run_id}/trace", response_model=AgentTraceResponse)
def get_run_trace(
    agent_id: str,
    run_id: str,
    service: AgentTraceService = Depends(get_trace_service),
) -> AgentTraceResponse:
    """Retrieve operational events logged for a specific run."""
    try:
        trace = service.get_trace(run_id)
        return AgentTraceResponse(
            run_id=trace.run_id,
            events=trace.events,
            total_events=len(trace.events),
        )
    except AgentError as e:
        _handle_agent_error(e)
        raise


# ==================================================
# DELEGATION ENDPOINTS
# ==================================================


@router.post(
    "/{agent_id}/delegations",
    response_model=AgentDelegationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_delegation(
    agent_id: str,
    req: CreateDelegationRequest,
    service: AgentDelegationService = Depends(get_delegation_service),
) -> AgentDelegationResponse:
    """Create a sub-task delegation from parent agent to child agent."""
    try:
        delegation = service.delegate_task(
            parent_agent_id=agent_id,
            child_agent_id=req.child_agent_id,
            task_id=req.task_id,
            parent_run_id=req.parent_run_id,
            reason=req.reason,
        )
        return AgentDelegationResponse(
            delegation_id=delegation.delegation_id,
            parent_agent_id=delegation.parent_agent_id,
            child_agent_id=delegation.child_agent_id,
            task_id=delegation.task_id,
            parent_run_id=delegation.parent_run_id,
            child_run_id=delegation.child_run_id,
            reason=delegation.reason,
            status=delegation.status.value,
            created_at=delegation.created_at,
            completed_at=delegation.completed_at,
        )
    except AgentError as e:
        _handle_agent_error(e)
        raise


@router.get("/{agent_id}/delegations", response_model=list[AgentDelegationResponse])
def list_delegations(
    agent_id: str,
    service: AgentDelegationService = Depends(get_delegation_service),
) -> list[AgentDelegationResponse]:
    """List delegations where agent is parent or child."""
    try:
        delegations = service.get_delegations_for_agent(agent_id)
        return [
            AgentDelegationResponse(
                delegation_id=d.delegation_id,
                parent_agent_id=d.parent_agent_id,
                child_agent_id=d.child_agent_id,
                task_id=d.task_id,
                parent_run_id=d.parent_run_id,
                child_run_id=d.child_run_id,
                reason=d.reason,
                status=d.status.value,
                created_at=d.created_at,
                completed_at=d.completed_at,
            )
            for d in delegations
        ]
    except AgentError as e:
        _handle_agent_error(e)
        raise
