"""Unit tests for Module 14 Tool Registry domain models, schemas, and exceptions."""

import pytest

from max.tools.domain.enums import ToolCategory, ToolRiskLevel, ToolStatus
from max.tools.domain.exceptions import InvalidToolDefinitionError
from max.tools.domain.tool import (
    Tool,
    ToolFieldDescriptor,
    ToolInputSchema,
    ToolOutputSchema,
)


def test_tool_domain_creation_and_validation() -> None:
    """Test valid Tool creation and validation logic."""
    input_schema = ToolInputSchema(
        fields=[ToolFieldDescriptor(name="msg", type="string", required=True)]
    )
    output_schema = ToolOutputSchema(
        fields=[ToolFieldDescriptor(name="res", type="string", required=True)]
    )

    tool = Tool(
        name="test.tool",
        description="A test tool definition",
        category=ToolCategory.UTILITY,
        input_schema=input_schema,
        output_schema=output_schema,
    )

    assert tool.id.startswith("tool_")
    assert tool.name == "test.tool"
    assert tool.status == ToolStatus.REGISTERED
    assert tool.risk_level == ToolRiskLevel.LOW

    descriptor = tool.to_descriptor()
    assert descriptor.name == "test.tool"
    assert descriptor.category == ToolCategory.UTILITY


def test_tool_domain_invalid_name_fails() -> None:
    """Test that tool names with spaces raise InvalidToolDefinitionError."""
    with pytest.raises(InvalidToolDefinitionError, match="must not contain spaces"):
        Tool(name="invalid tool name", description="Invalid name test")


def test_tool_domain_empty_description_fails() -> None:
    """Test that empty description raises InvalidToolDefinitionError."""
    with pytest.raises(InvalidToolDefinitionError, match="must have a non-empty description"):
        Tool(name="valid.name", description="   ")
