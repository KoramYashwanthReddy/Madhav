from max.tools.domain.enums import ToolCapability, ToolInvocationStatus
from max.tools.domain.invocation import ToolInvocationRequest
from max.tools.repositories.invocation_repository import InMemoryToolInvocationRepository
from max.tools.repositories.tool_repository import InMemoryToolRepository
from max.tools.repositories.trace_repository import InMemoryToolTraceRepository
from max.tools.services.discovery_service import ToolDiscoveryService
from max.tools.services.invocation_service import ToolInvocationService
from max.tools.services.registry import ToolRegistryService
from max.tools.services.resolver import ToolResolver
from max.tools.services.trace_service import ToolTraceService


def test_tool_registry_full_e2e_acceptance_flow() -> None:
    """Validate full acceptance scenario from Item 66 of Module 14 specification."""
    tool_repo = InMemoryToolRepository()
    inv_repo = InMemoryToolInvocationRepository()
    trace_repo = InMemoryToolTraceRepository()

    trace_svc = ToolTraceService(trace_repo)
    reg_svc = ToolRegistryService(
        tool_repository=tool_repo, trace_service=trace_svc, auto_load_dev_tools=True
    )
    disc_svc = ToolDiscoveryService(tool_repository=tool_repo)
    resolver_svc = ToolResolver(tool_repository=tool_repo, trace_service=trace_svc)
    inv_svc = ToolInvocationService(
        invocation_repository=inv_repo,
        tool_repository=tool_repo,
        resolver=resolver_svc,
        trace_service=trace_svc,
    )

    # 1. Preloaded echo.test:v1 exists and is validated
    echo_tool = reg_svc.get_tool("echo.test:v1")
    assert echo_tool.name == "echo.test"

    # 2. Activate tool
    active_tool = reg_svc.activate_tool(echo_tool.id)
    assert active_tool.status == "ACTIVE"

    # 3. Discover tool using capability = TEXT_TRANSFORMATION
    descriptors = disc_svc.discover_descriptors_for_capabilities(
        [ToolCapability.TEXT_TRANSFORMATION]
    )
    assert any(d.name == "echo.test" for d in descriptors)

    # 4. Resolve tool
    resolved = resolver_svc.resolve_tool("echo.test")
    assert resolved.is_active is True

    # 5. Invoke tool with valid arguments
    req = ToolInvocationRequest(
        tool_name=resolved.name,
        arguments={"message": "Acceptance Test Payload"},
        agent_id="agent_e2e_coordinator",
        task_id="task_e2e_123",
        owner_id="user_e2e",
    )
    result = inv_svc.invoke_tool(req)

    # 6. Verify result & output validation
    assert result.status == ToolInvocationStatus.COMPLETED
    assert result.output == {"message": "Acceptance Test Payload"}
    assert result.duration_seconds >= 0.0

    # 7. Verify trace operational events logged cleanly
    trace = trace_svc.get_trace_for_invocation(result.invocation_id)
    assert len(trace.events) > 0
    event_types = [e.event_type.value for e in trace.events]
    assert "INVOCATION_CREATED" in event_types
    assert "ARGUMENTS_VALIDATED" in event_types
    assert "PERMISSION_REQUESTED" in event_types
    assert "EXECUTION_STARTED" in event_types
    assert "EXECUTION_COMPLETED" in event_types
    assert "INVOCATION_COMPLETED" in event_types
