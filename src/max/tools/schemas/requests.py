"""FastAPI Pydantic request DTO schemas for Module 14 Tool Registry API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from max.tools.domain.enums import (
    ToolCapability,
    ToolCategory,
    ToolExecutionMode,
    ToolRiskLevel,
    ToolSource,
)
from max.tools.domain.tool import (
    ToolConfiguration,
    ToolInputSchema,
    ToolOutputSchema,
)


class RegisterToolRequest(BaseModel):
    """Request DTO to register a new tool definition."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Machine-readable tool name (e.g. 'echo.test')")
    description: str = Field(description="Purpose and usage description")
    version: str = Field(default="1.0.0", description="Semantic version string")
    category: ToolCategory = Field(
        default=ToolCategory.UTILITY, description="Category classification"
    )
    capabilities: list[ToolCapability] = Field(
        default_factory=lambda: [ToolCapability.TEXT_TRANSFORMATION],
        description="Supported capabilities",
    )
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Risk level metadata")
    source: ToolSource = Field(default=ToolSource.USER_DEFINED, description="Tool origin source")
    input_schema: ToolInputSchema = Field(
        default_factory=ToolInputSchema, description="Input schema"
    )
    output_schema: ToolOutputSchema = Field(
        default_factory=ToolOutputSchema, description="Output schema"
    )
    configuration: ToolConfiguration = Field(
        default_factory=ToolConfiguration, description="Configuration"
    )
    owner_id: str = Field(default="system", description="Owner user ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary safe metadata")


class UpdateToolRequest(BaseModel):
    """Request DTO to update an existing tool definition."""

    model_config = ConfigDict(frozen=True)

    description: str | None = Field(default=None, description="Updated description")
    category: ToolCategory | None = Field(default=None, description="Updated category")
    capabilities: list[ToolCapability] | None = Field(
        default=None, description="Updated capabilities"
    )
    risk_level: ToolRiskLevel | None = Field(default=None, description="Updated risk level")
    configuration: ToolConfiguration | None = Field(
        default=None, description="Updated configuration"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Updated metadata")


class ResolveToolRequest(BaseModel):
    """Request DTO to resolve a tool reference."""

    model_config = ConfigDict(frozen=True)

    tool_identifier: str = Field(description="Tool ID, name, or name:version reference")
    version: str | None = Field(default=None, description="Optional explicit version requirement")
    required_capability: ToolCapability | None = Field(
        default=None, description="Optional capability requirement"
    )


class CreateToolInvocationRequest(BaseModel):
    """Request DTO to invoke a tool."""

    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(description="Name or ID of target tool")
    tool_version: str | None = Field(default=None, description="Target version or latest")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Input arguments dictionary"
    )
    execution_mode: ToolExecutionMode = Field(
        default=ToolExecutionMode.DRY_RUN, description="Execution mode"
    )
    client_request_id: str | None = Field(default=None, description="Idempotency key")

    agent_id: str | None = Field(default=None, description="Calling agent ID")
    run_id: str | None = Field(default=None, description="Calling agent run ID")
    task_id: str | None = Field(default=None, description="Linked task ID")
    plan_id: str | None = Field(default=None, description="Linked plan ID")
    plan_step_id: str | None = Field(default=None, description="Linked plan step ID")
    conversation_id: str | None = Field(default=None, description="Linked conversation ID")
    owner_id: str = Field(default="user_default", description="Owner user ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary request metadata")
