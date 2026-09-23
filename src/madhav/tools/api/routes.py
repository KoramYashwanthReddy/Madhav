"""FastAPI REST API routes for Module 14 Tool Registry."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from madhav.tools.domain.enums import (
    ToolCapability,
    ToolCategory,
    ToolInvocationStatus,
    ToolStatus,
)
from madhav.tools.domain.exceptions import (
    DuplicateToolError,
    InvalidToolDefinitionError,
    ToolArgumentValidationError,
    ToolCapabilityError,
    ToolError,
    ToolExecutionBoundaryError,
    ToolInactiveError,
    ToolInvocationNotFoundError,
    ToolInvocationStateError,
    ToolNotFoundError,
    ToolOutputValidationError,
    ToolPermissionRequiredError,
)
from madhav.tools.domain.invocation import ToolInvocationRequest
from madhav.tools.schemas.requests import (
    CreateToolInvocationRequest,
    RegisterToolRequest,
    ResolveToolRequest,
    UpdateToolRequest,
)
from madhav.tools.schemas.responses import (
    ToolDescriptorResponse,
    ToolInvocationResponse,
    ToolListResponse,
    ToolResolveResponse,
    ToolResponse,
    ToolTraceResponse,
)
from madhav.tools.services.discovery_service import ToolDiscoveryService
from madhav.tools.services.invocation_service import ToolInvocationService
from madhav.tools.services.registry import ToolRegistryService
from madhav.tools.services.resolver import ToolResolver
from madhav.tools.services.trace_service import ToolTraceService

router = APIRouter(prefix="/tools", tags=["Tool Registry"])

_registry_service: ToolRegistryService | None = None
_discovery_service: ToolDiscoveryService | None = None
_resolver_service: ToolResolver | None = None
_invocation_service: ToolInvocationService | None = None
_trace_service: ToolTraceService | None = None


def get_registry_service() -> ToolRegistryService:
    global _registry_service
    if _registry_service is None:
        _registry_service = ToolRegistryService()
    return _registry_service


def get_discovery_service() -> ToolDiscoveryService:
    global _discovery_service
    if _discovery_service is None:
        reg_svc = get_registry_service()
        _discovery_service = ToolDiscoveryService(tool_repository=reg_svc.repository)
    return _discovery_service


def get_trace_service() -> ToolTraceService:
    global _trace_service
    if _trace_service is None:
        _trace_service = ToolTraceService()
    return _trace_service


def get_resolver_service() -> ToolResolver:
    global _resolver_service
    if _resolver_service is None:
        reg_svc = get_registry_service()
        trace_svc = get_trace_service()
        _resolver_service = ToolResolver(tool_repository=reg_svc.repository, trace_service=trace_svc)
    return _resolver_service


def get_invocation_service() -> ToolInvocationService:
    global _invocation_service
    if _invocation_service is None:
        reg_svc = get_registry_service()
        trace_svc = get_trace_service()
        resolver_svc = get_resolver_service()
        _invocation_service = ToolInvocationService(
            tool_repository=reg_svc.repository,
            resolver=resolver_svc,
            trace_service=trace_svc,
        )
    return _invocation_service


def _handle_tool_error(e: ToolError) -> None:
    if isinstance(e, (ToolNotFoundError, ToolInvocationNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif isinstance(e, DuplicateToolError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    elif isinstance(e, (InvalidToolDefinitionError, ToolInvocationStateError)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    elif isinstance(
        e,
        (
            ToolArgumentValidationError,
            ToolOutputValidationError,
            ToolCapabilityError,
            ToolInactiveError,
            ToolPermissionRequiredError,
            ToolExecutionBoundaryError,
        ),
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _to_tool_response(tool: Any) -> ToolResponse:
    return ToolResponse(
        id=tool.id,
        name=tool.name,
        version=tool.version,
        description=tool.description,
        category=tool.category,
        capabilities=tool.capabilities,
        status=tool.status,
        risk_level=tool.risk_level,
        source=tool.source,
        input_schema=tool.input_schema,
        output_schema=tool.output_schema,
        configuration=tool.configuration,
        availability=tool.availability,
        owner_id=tool.owner_id,
        metadata=tool.metadata,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
    )


def _to_invocation_response(inv: Any) -> ToolInvocationResponse:
    return ToolInvocationResponse(
        invocation_id=inv.invocation_id,
        tool_id=inv.tool_id,
        tool_version=inv.tool_version,
        status=inv.status,
        execution_mode=inv.execution_mode,
        arguments=inv.arguments,
        context=inv.context,
        client_request_id=inv.client_request_id,
        started_at=inv.started_at,
        completed_at=inv.completed_at,
        output=inv.result.output if inv.result else None,
        failure=inv.failure,
        duration_seconds=inv.result.duration_seconds if inv.result else 0.0,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


# ==================================================
# TOOL REGISTRATION & LIFECYCLE ENDPOINTS
# ==================================================


@router.post("", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
def register_tool(
    req: RegisterToolRequest,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Register a new Tool definition."""
    try:
        tool = service.register_tool(
            name=req.name,
            description=req.description,
            version=req.version,
            category=req.category,
            capabilities=req.capabilities,
            risk_level=req.risk_level,
            source=req.source,
            input_schema=req.input_schema,
            output_schema=req.output_schema,
            configuration=req.configuration,
            owner_id=req.owner_id,
            metadata=req.metadata,
        )
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.get("", response_model=ToolListResponse)
def list_tools(
    category: ToolCategory | None = Query(default=None, description="Filter by tool category"),
    capability: ToolCapability | None = Query(default=None, description="Filter by capability"),
    status_filter: ToolStatus | None = Query(default=None, alias="status", description="Filter by status"),
    search_query: str | None = Query(default=None, alias="q", description="Search keyword query"),
    owner_id: str | None = Query(default=None, description="Filter by owner ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Page size limit"),
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolListResponse:
    """List tool definitions with filtering and pagination."""
    offset = (page - 1) * page_size
    tools, total = service.list_tools(
        category=category,
        capability=capability,
        status=status_filter,
        search_query=search_query,
        owner_id=owner_id,
        limit=page_size,
        offset=offset,
    )
    return ToolListResponse(
        tools=[_to_tool_response(t) for t in tools],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/search", response_model=list[ToolDescriptorResponse])
def search_tool_descriptors(
    category: ToolCategory | None = Query(default=None, description="Filter category"),
    capability: ToolCapability | None = Query(default=None, description="Filter capability"),
    query: str | None = Query(default=None, description="Search term query"),
    service: ToolDiscoveryService = Depends(get_discovery_service),
) -> list[ToolDescriptorResponse]:
    """Search available tool descriptors for AI context."""
    descriptors, _ = service.search_tools(
        category=category, capability=capability, query=query, active_only=True
    )
    return [
        ToolDescriptorResponse(
            id=d.id,
            name=d.name,
            version=d.version,
            category=d.category,
            capabilities=d.capabilities,
            description=d.description,
            risk_level=d.risk_level,
            status=d.status,
            input_schema=d.input_schema,
            output_schema=d.output_schema,
        )
        for d in descriptors
    ]


@router.get("/capabilities", response_model=list[ToolDescriptorResponse])
def discover_by_capability(
    capability: ToolCapability = Query(description="Target capability to discover"),
    service: ToolDiscoveryService = Depends(get_discovery_service),
) -> list[ToolDescriptorResponse]:
    """Discover tool descriptors supporting a specific capability."""
    descriptors = service.discover_descriptors_for_capabilities([capability])
    return [
        ToolDescriptorResponse(
            id=d.id,
            name=d.name,
            version=d.version,
            category=d.category,
            capabilities=d.capabilities,
            description=d.description,
            risk_level=d.risk_level,
            status=d.status,
            input_schema=d.input_schema,
            output_schema=d.output_schema,
        )
        for d in descriptors
    ]


@router.post("/resolve", response_model=ToolResolveResponse)
def resolve_tool(
    req: ResolveToolRequest,
    service: ToolResolver = Depends(get_resolver_service),
) -> ToolResolveResponse:
    """Resolve a tool reference to an active ResolvedTool object."""
    try:
        resolved = service.resolve_tool(
            tool_identifier=req.tool_identifier,
            version=req.version,
            required_capability=req.required_capability,
        )
        return ToolResolveResponse(
            tool_id=resolved.tool_id,
            name=resolved.name,
            version=resolved.version,
            is_active=resolved.is_active,
            tool=_to_tool_response(resolved.tool),
            resolved_at=resolved.resolved_at,
        )
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.get("/{tool_id}", response_model=ToolResponse)
def get_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Retrieve tool definition by ID."""
    try:
        tool = service.get_tool(tool_id)
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.patch("/{tool_id}", response_model=ToolResponse)
def update_tool(
    tool_id: str,
    req: UpdateToolRequest,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Update properties of a tool definition."""
    try:
        tool = service.update_tool(
            tool_id=tool_id,
            description=req.description,
            category=req.category,
            capabilities=req.capabilities,
            risk_level=req.risk_level,
            configuration=req.configuration,
            metadata=req.metadata,
        )
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> None:
    """Archive and delete tool definition."""
    try:
        service.archive_tool(tool_id)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.post("/{tool_id}/activate", response_model=ToolResponse)
def activate_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Transition tool status to ACTIVE."""
    try:
        tool = service.activate_tool(tool_id)
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.post("/{tool_id}/disable", response_model=ToolResponse)
def disable_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Transition tool status to DISABLED."""
    try:
        tool = service.disable_tool(tool_id)
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.post("/{tool_id}/deprecate", response_model=ToolResponse)
def deprecate_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Transition tool status to DEPRECATED."""
    try:
        tool = service.deprecate_tool(tool_id)
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.post("/{tool_id}/archive", response_model=ToolResponse)
def archive_tool(
    tool_id: str,
    service: ToolRegistryService = Depends(get_registry_service),
) -> ToolResponse:
    """Transition tool status to ARCHIVED."""
    try:
        tool = service.archive_tool(tool_id)
        return _to_tool_response(tool)
    except ToolError as e:
        _handle_tool_error(e)
        raise


# ==================================================
# INVOCATION ENDPOINTS
# ==================================================


@router.post("/invocations", response_model=ToolInvocationResponse, status_code=status.HTTP_201_CREATED)
def create_invocation(
    req: CreateToolInvocationRequest,
    service: ToolInvocationService = Depends(get_invocation_service),
) -> ToolInvocationResponse:
    """Execute a tool invocation pipeline."""
    try:
        inv_req = ToolInvocationRequest(
            tool_name=req.tool_name,
            tool_version=req.tool_version,
            arguments=req.arguments,
            execution_mode=req.execution_mode,
            client_request_id=req.client_request_id,
            agent_id=req.agent_id,
            run_id=req.run_id,
            task_id=req.task_id,
            plan_id=req.plan_id,
            plan_step_id=req.plan_step_id,
            conversation_id=req.conversation_id,
            owner_id=req.owner_id,
            metadata=req.metadata,
        )
        result = service.invoke_tool(inv_req)
        inv = service.get_invocation(result.invocation_id)
        return _to_invocation_response(inv)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.get("/invocations", response_model=list[ToolInvocationResponse])
def list_invocations(
    tool_id: str | None = Query(default=None, description="Filter by tool ID"),
    agent_id: str | None = Query(default=None, description="Filter by agent ID"),
    run_id: str | None = Query(default=None, description="Filter by run ID"),
    task_id: str | None = Query(default=None, description="Filter by task ID"),
    status_filter: ToolInvocationStatus | None = Query(default=None, alias="status", description="Filter status"),
    page: int = Query(default=1, ge=1, description="Page index"),
    page_size: int = Query(default=50, ge=1, le=100, description="Page size limit"),
    service: ToolInvocationService = Depends(get_invocation_service),
) -> list[ToolInvocationResponse]:
    """List tool invocations with filters and pagination."""
    offset = (page - 1) * page_size
    invocations, _ = service.list_invocations(
        tool_id=tool_id,
        agent_id=agent_id,
        run_id=run_id,
        task_id=task_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    return [_to_invocation_response(i) for i in invocations]


@router.get("/invocations/{invocation_id}", response_model=ToolInvocationResponse)
def get_invocation(
    invocation_id: str,
    service: ToolInvocationService = Depends(get_invocation_service),
) -> ToolInvocationResponse:
    """Retrieve details of a tool invocation record."""
    try:
        inv = service.get_invocation(invocation_id)
        return _to_invocation_response(inv)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.post("/invocations/{invocation_id}/cancel", response_model=ToolInvocationResponse)
def cancel_invocation(
    invocation_id: str,
    reason: str = Query(default="Cancelled via API request", description="Reason for cancellation"),
    service: ToolInvocationService = Depends(get_invocation_service),
) -> ToolInvocationResponse:
    """Cancel an active or pending tool invocation."""
    try:
        inv = service.cancel_invocation(invocation_id, reason=reason)
        return _to_invocation_response(inv)
    except ToolError as e:
        _handle_tool_error(e)
        raise


@router.get("/invocations/{invocation_id}/trace", response_model=ToolTraceResponse)
def get_invocation_trace(
    invocation_id: str,
    service: ToolTraceService = Depends(get_trace_service),
) -> ToolTraceResponse:
    """Retrieve audit trace event timeline for a tool invocation."""
    trace = service.get_trace_for_invocation(invocation_id)
    return ToolTraceResponse(
        invocation_id=trace.invocation_id,
        events=trace.events,
        total_events=len(trace.events),
    )
