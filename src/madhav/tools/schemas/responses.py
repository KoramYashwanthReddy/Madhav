"""FastAPI Pydantic response DTO schemas for Module 14 Tool Registry API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from madhav.tools.domain.enums import (
    ToolCapability,
    ToolCategory,
    ToolExecutionMode,
    ToolInvocationStatus,
    ToolRiskLevel,
    ToolSource,
    ToolStatus,
)
from madhav.tools.domain.invocation import ToolInvocationContext, ToolInvocationFailure
from madhav.tools.domain.tool import (
    ToolAvailability,
    ToolConfiguration,
    ToolInputSchema,
    ToolOutputSchema,
)
from madhav.tools.domain.trace import ToolEvent


class ToolResponse(BaseModel):
    """Response DTO representing a registered Tool entity."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Unique tool ID")
    name: str = Field(description="Tool name")
    version: str = Field(description="Version string")
    description: str = Field(description="Purpose description")
    category: ToolCategory = Field(description="Category classification")
    capabilities: list[ToolCapability] = Field(description="Supported capabilities")
    status: ToolStatus = Field(description="Lifecycle status")
    risk_level: ToolRiskLevel = Field(description="Risk level metadata")
    source: ToolSource = Field(description="Tool source classification")
    input_schema: ToolInputSchema = Field(description="Input arguments schema")
    output_schema: ToolOutputSchema = Field(description="Output result schema")
    configuration: ToolConfiguration = Field(description="Configuration")
    availability: ToolAvailability = Field(description="Availability state")
    owner_id: str = Field(description="Owner ID")
    metadata: dict[str, Any] = Field(description="Safe metadata")
    created_at: datetime = Field(description="Created timestamp")
    updated_at: datetime = Field(description="Updated timestamp")


class ToolListResponse(BaseModel):
    """Paginated response wrapper for tools listing."""

    model_config = ConfigDict(frozen=True)

    tools: list[ToolResponse] = Field(description="List of tool records")
    total: int = Field(description="Total matching count")
    page: int = Field(description="Current page index")
    page_size: int = Field(description="Current page size limit")


class ToolDescriptorResponse(BaseModel):
    """Compact response descriptor for AI model context consumption."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Tool ID")
    name: str = Field(description="Tool name")
    version: str = Field(description="Tool version")
    category: ToolCategory = Field(description="Tool category")
    capabilities: list[ToolCapability] = Field(description="Capabilities")
    description: str = Field(description="Description")
    risk_level: ToolRiskLevel = Field(description="Risk level")
    status: ToolStatus = Field(description="Status")
    input_schema: ToolInputSchema = Field(description="Input schema")
    output_schema: ToolOutputSchema = Field(description="Output schema")


class ToolResolveResponse(BaseModel):
    """Response DTO for tool resolution."""

    model_config = ConfigDict(frozen=True)

    tool_id: str = Field(description="Resolved tool ID")
    name: str = Field(description="Tool name")
    version: str = Field(description="Resolved version")
    is_active: bool = Field(description="Active state")
    tool: ToolResponse = Field(description="Full resolved tool entity")
    resolved_at: datetime = Field(description="Resolution timestamp")


class ToolInvocationResponse(BaseModel):
    """Response DTO representing a tool invocation lifecycle record."""

    model_config = ConfigDict(frozen=True)

    invocation_id: str = Field(description="Unique invocation ID")
    tool_id: str = Field(description="Tool ID")
    tool_version: str = Field(description="Tool version")
    status: ToolInvocationStatus = Field(description="Current invocation status")
    execution_mode: ToolExecutionMode = Field(description="Execution mode")
    arguments: dict[str, Any] = Field(description="Arguments dictionary")
    context: ToolInvocationContext = Field(description="Traceability pointers")
    client_request_id: str | None = Field(default=None, description="Idempotency key")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    output: dict[str, Any] | None = Field(default=None, description="Result output dictionary if completed")
    failure: ToolInvocationFailure | None = Field(default=None, description="Failure detail if failed")
    duration_seconds: float = Field(default=0.0, description="Execution duration in seconds")
    created_at: datetime = Field(description="Created timestamp")
    updated_at: datetime = Field(description="Updated timestamp")


class ToolTraceResponse(BaseModel):
    """Response DTO representing audit trace timeline of events for an invocation."""

    model_config = ConfigDict(frozen=True)

    invocation_id: str = Field(description="Target invocation ID")
    events: list[ToolEvent] = Field(description="Chronological event log")
    total_events: int = Field(description="Total event count")
