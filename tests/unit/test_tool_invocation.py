"""Unit tests for ToolInvocationService, validators, dev tools, and boundary protections."""

import pytest

from madhav.tools.domain.enums import ToolInvocationStatus
from madhav.tools.domain.exceptions import (
    ToolArgumentValidationError,
    ToolOutputValidationError,
)
from madhav.tools.domain.invocation import ToolInvocationRequest
from madhav.tools.domain.tool import (
    ToolFieldDescriptor,
    ToolInputSchema,
    ToolOutputSchema,
)
from madhav.tools.repositories.invocation_repository import InMemoryToolInvocationRepository
from madhav.tools.repositories.tool_repository import InMemoryToolRepository
from madhav.tools.services.invocation_service import ToolInvocationService
from madhav.tools.services.registry import ToolRegistryService
from madhav.tools.validators.argument_validator import ToolArgumentValidator
from madhav.tools.validators.output_validator import ToolOutputValidator


@pytest.fixture
def repo():
    return InMemoryToolRepository()


@pytest.fixture
def inv_repo():
    return InMemoryToolInvocationRepository()


@pytest.fixture
def registry_svc(repo):
    return ToolRegistryService(tool_repository=repo, auto_load_dev_tools=True)


@pytest.fixture
def inv_service(repo, inv_repo, registry_svc):
    return ToolInvocationService(invocation_repository=inv_repo, tool_repository=repo)


def test_argument_and_output_validators() -> None:
    """Test schema validation enforcement."""
    input_schema = ToolInputSchema(
        fields=[
            ToolFieldDescriptor(name="count", type="integer", required=True, min_value=1),
            ToolFieldDescriptor(name="mode", type="string", required=False, allowed_values=["fast", "slow"]),
        ]
    )

    # Valid arguments
    ToolArgumentValidator.validate("test_tool", {"count": 5, "mode": "fast"}, input_schema)

    # Missing required argument fails
    with pytest.raises(ToolArgumentValidationError, match="Missing required argument"):
        ToolArgumentValidator.validate("test_tool", {"mode": "fast"}, input_schema)

    # Type mismatch fails
    with pytest.raises(ToolArgumentValidationError, match="expected integer"):
        ToolArgumentValidator.validate("test_tool", {"count": "five"}, input_schema)

    # Invalid enum value fails
    with pytest.raises(ToolArgumentValidationError, match="not in allowed values"):
        ToolArgumentValidator.validate("test_tool", {"count": 2, "mode": "invalid_mode"}, input_schema)

    output_schema = ToolOutputSchema(
        fields=[ToolFieldDescriptor(name="result", type="string", required=True)]
    )

    # Valid output
    ToolOutputValidator.validate("test_tool", {"result": "success"}, output_schema)

    # Missing required output fails
    with pytest.raises(ToolOutputValidationError, match="Missing required output field"):
        ToolOutputValidator.validate("test_tool", {}, output_schema)


def test_dev_tool_echo_invocation(inv_service) -> None:
    """Test safe execution of echo.test development tool."""
    req = ToolInvocationRequest(
        tool_name="echo.test",
        arguments={"message": "Hello Madhav"},
    )

    result = inv_service.invoke_tool(req)
    assert result.status == ToolInvocationStatus.COMPLETED
    assert result.output == {"message": "Hello Madhav"}
    assert result.duration_seconds >= 0.0


def test_dev_tool_math_calculate(inv_service) -> None:
    """Test safe arithmetic execution (add, divide, division by zero)."""
    # Addition
    req_add = ToolInvocationRequest(
        tool_name="math.calculate",
        arguments={"operation": "add", "left": 10.5, "right": 4.5},
    )
    res_add = inv_service.invoke_tool(req_add)
    assert res_add.status == ToolInvocationStatus.COMPLETED
    assert res_add.output == {"result": 15.0}

    # Division by zero failure
    req_div_zero = ToolInvocationRequest(
        tool_name="math.calculate",
        arguments={"operation": "divide", "left": 10.0, "right": 0.0},
    )
    res_div_zero = inv_service.invoke_tool(req_div_zero)
    assert res_div_zero.status == ToolInvocationStatus.FAILED


def test_dev_tool_text_transform(inv_service) -> None:
    """Test safe text transformation operations."""
    req = ToolInvocationRequest(
        tool_name="text.transform",
        arguments={"operation": "uppercase", "text": "hello world"},
    )
    res = inv_service.invoke_tool(req)
    assert res.status == ToolInvocationStatus.COMPLETED
    assert res.output == {"result": "HELLO WORLD"}


def test_high_risk_future_tool_boundary_rejection(inv_service) -> None:
    """Test that future high risk tools (terminal.execute) terminate at permission/execution boundary."""
    req = ToolInvocationRequest(
        tool_name="terminal.execute",
        arguments={"command": "ls -la"},
    )
    res = inv_service.invoke_tool(req)
    # Terminal stub is DISABLED by default, so it fails at resolution/permission check
    assert res.status == ToolInvocationStatus.FAILED
