"""Integration tests for Module 13 Agent Engine and Module 14 Tool Registry."""

import pytest

from madhav.agents.domain.agent import ToolRequestIntent
from madhav.tools.domain.enums import ToolInvocationStatus
from madhav.tools.repositories.invocation_repository import InMemoryToolInvocationRepository
from madhav.tools.repositories.tool_repository import InMemoryToolRepository
from madhav.tools.services.agent_integration import AgentToolIntegrationService
from madhav.tools.services.invocation_service import ToolInvocationService
from madhav.tools.services.registry import ToolRegistryService


@pytest.fixture
def integration_service():
    tool_repo = InMemoryToolRepository()
    inv_repo = InMemoryToolInvocationRepository()
    ToolRegistryService(tool_repository=tool_repo, auto_load_dev_tools=True)
    inv_svc = ToolInvocationService(invocation_repository=inv_repo, tool_repository=tool_repo)
    return AgentToolIntegrationService(invocation_service=inv_svc)


def test_agent_tool_request_intent_integration(integration_service) -> None:
    """Test translating Module 13 Agent ToolRequestIntent into Module 14 ToolInvocationResult."""
    intent = ToolRequestIntent(
        tool_name="math.calculate",
        requested_capability="MATH_CALCULATION",
        parameters={"operation": "multiply", "left": 6.0, "right": 7.0},
        agent_id="agent_coordinator_123",
        run_id="run_456",
        task_id="task_789",
        reason="Agent requested math calculation capability",
    )

    result = integration_service.process_agent_tool_request(intent)

    assert result.status == ToolInvocationStatus.COMPLETED
    assert result.output == {"result": 42.0}
    assert result.tool_id.startswith("math.calculate")
