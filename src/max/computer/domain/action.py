"""Domain models for computer actions, requests, results, failures, and sequences."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.computer.domain.enums import (
    ComputerActionFailureReason,
    ComputerActionStatus,
    ComputerActionType,
)


class ComputerActionRequest(BaseModel):
    """Structured request payload for a computer control action."""

    action_id: str = Field(
        default_factory=lambda: f"cact_{uuid.uuid4().hex[:12]}",
        description="Unique computer action request ID",
    )
    action_type: ComputerActionType = Field(..., description="Target computer action type")
    target: str | None = Field(default=None, description="Action target (window_id, display_id, resource path, etc.)")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters (x, y, text, button, etc.)")
    agent_id: str | None = Field(default=None, description="Requesting agent ID")
    agent_run_id: str | None = Field(default=None, description="Agent run ID")
    task_id: str | None = Field(default=None, description="Task ID reference")
    plan_id: str | None = Field(default=None, description="Plan ID reference")
    conversation_id: str | None = Field(default=None, description="Conversation ID reference")
    owner_id: str = Field(default="default_owner", description="Resource owner boundary identity")
    permission_decision_id: str | None = Field(
        default=None, description="Module 15 authorization decision token ID"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Request creation timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class ComputerActionResult(BaseModel):
    """Normalized result outcome of an executed computer action."""

    action_id: str = Field(..., description="Target action ID")
    action_type: ComputerActionType = Field(..., description="Executed action type")
    status: ComputerActionStatus = Field(..., description="Action outcome status")
    target: str | None = Field(default=None, description="Target key or handle")
    observed_state: dict[str, Any] = Field(default_factory=dict, description="Observed state parameters after action")
    duration: float = Field(default=0.0, description="Execution duration in seconds")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Result timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class ComputerActionFailure(BaseModel):
    """Structured failure representation for a failed computer action."""

    action_id: str = Field(..., description="Associated action ID")
    action_type: ComputerActionType = Field(..., description="Associated action type")
    reason: ComputerActionFailureReason = Field(..., description="Structured failure category")
    message: str = Field(..., description="Human-readable failure summary")
    details: dict[str, Any] = Field(default_factory=dict, description="Diagnostic failure details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Failure timestamp"
    )



class ComputerAction(BaseModel):
    """Full lifecycle model for a computer control action."""

    action_id: str = Field(
        default_factory=lambda: f"cact_{uuid.uuid4().hex[:12]}",
        description="Unique action ID",
    )
    request: ComputerActionRequest = Field(..., description="Underlying action request")
    status: ComputerActionStatus = Field(default=ComputerActionStatus.CREATED, description="Lifecycle status")
    result: ComputerActionResult | None = Field(default=None, description="Action result if completed")
    failure: ComputerActionFailure | None = Field(default=None, description="Failure record if failed")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )


class ComputerActionSequence(BaseModel):
    """Ordered sequence of computer control actions executed sequentially."""

    sequence_id: str = Field(
        default_factory=lambda: f"seq_{uuid.uuid4().hex[:12]}",
        description="Unique sequence identifier",
    )
    actions: list[ComputerActionRequest] = Field(..., description="Ordered list of action requests")
    max_length: int = Field(default=20, description="Maximum allowed actions in this sequence")
    stop_on_failure: bool = Field(default=True, description="Whether to halt sequence execution if any action fails")
    status: ComputerActionStatus = Field(default=ComputerActionStatus.CREATED, description="Sequence status")
    completed_actions: list[ComputerActionResult] = Field(default_factory=list, description="Executed action results")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Sequence creation timestamp"
    )
    completed_at: datetime | None = Field(default=None, description="Sequence completion timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Sequence metadata tags")
