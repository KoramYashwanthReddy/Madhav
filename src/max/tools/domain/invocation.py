"""Tool invocation models, context, requests, and results."""

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from max.tools.domain.enums import (
    ToolExecutionMode,
    ToolFailureCategory,
    ToolInvocationStatus,
)


class ToolInvocationContext(BaseModel):
    """Contextual metadata references linked to a tool invocation."""

    model_config = ConfigDict(frozen=True)

    plan_id: str | None = Field(default=None, description="Linked Module 11 Plan ID")
    plan_step_id: str | None = Field(default=None, description="Linked Plan Step ID")
    task_id: str | None = Field(default=None, description="Linked Module 12 Task ID")
    agent_id: str | None = Field(default=None, description="Linked Module 13 Agent ID")
    run_id: str | None = Field(default=None, description="Linked AgentRun ID")
    conversation_id: str | None = Field(default=None, description="Linked Conversation ID")
    owner_id: str = Field(default="user_default", description="Owner user ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary context metadata")


class ToolInvocationFailure(BaseModel):
    """Structured failure diagnosis for a tool invocation."""

    model_config = ConfigDict(frozen=True)

    error_code: str = Field(default="TOOL_INVOCATION_FAILED", description="Error taxonomy code")
    message: str = Field(description="Descriptive failure message")
    category: ToolFailureCategory = Field(
        default=ToolFailureCategory.INTERNAL_ERROR, description="Failure category taxonomy"
    )
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Failure timestamp")
    invocation_id: str | None = Field(default=None, description="Target invocation ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Diagnostic context metadata")


class ToolInvocationResult(BaseModel):
    """Structured outcome data produced upon tool invocation completion."""

    model_config = ConfigDict(frozen=True)

    invocation_id: str = Field(description="Unique invocation identifier")
    tool_id: str = Field(description="Tool ID invoked")
    status: ToolInvocationStatus = Field(description="Final invocation status")
    output: dict[str, Any] = Field(default_factory=dict, description="Validated output payload dictionary")
    duration_seconds: float = Field(default=0.0, ge=0.0, description="Invocation duration in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Outcome metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Result timestamp")
    completed_at: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class ToolInvocation(BaseModel):
    """Core domain entity representing a tool usage invocation request lifecycle."""

    model_config = ConfigDict(frozen=True)

    invocation_id: str = Field(
        default_factory=lambda: f"inv_{uuid4().hex[:12]}", description="Unique invocation identifier"
    )
    tool_id: str = Field(description="Target tool ID")
    tool_version: str = Field(default="1.0.0", description="Target tool version")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Input argument dictionary")
    execution_mode: ToolExecutionMode = Field(
        default=ToolExecutionMode.DRY_RUN, description="Execution mode"
    )
    status: ToolInvocationStatus = Field(
        default=ToolInvocationStatus.CREATED, description="Current lifecycle state"
    )
    client_request_id: str | None = Field(default=None, description="Idempotency key")

    context: ToolInvocationContext = Field(
        default_factory=ToolInvocationContext, description="Traceability context pointers"
    )

    started_at: datetime | None = Field(default=None, description="Execution start timestamp")
    completed_at: datetime | None = Field(default=None, description="Execution completion timestamp")

    result: ToolInvocationResult | None = Field(default=None, description="Result object if completed")
    failure: ToolInvocationFailure | None = Field(default=None, description="Failure object if failed")

    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary invocation metadata")


class ToolInvocationRequest(BaseModel):
    """Request DTO to initiate a tool invocation."""

    model_config = ConfigDict(frozen=True)

    tool_name: str = Field(description="Name or ID of target tool")
    tool_version: str | None = Field(default=None, description="Target version or latest")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Argument parameters")
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
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")
