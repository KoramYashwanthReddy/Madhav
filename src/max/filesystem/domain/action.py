"""Domain models for file operations, requests, results, failures, and lifecycle states."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.filesystem.domain.enums import (
    FileFailureReason,
    FileOperationStatus,
    FileOperationType,
)


class FileOperationRequest(BaseModel):
    """Structured request payload for a filesystem operation."""

    operation_id: str = Field(
        default_factory=lambda: f"fop_{uuid.uuid4().hex[:12]}",
        description="Unique file operation ID",
    )
    operation_type: FileOperationType = Field(..., description="Target file operation type")
    source: str = Field(..., description="Primary source target path")
    destination: str | None = Field(default=None, description="Optional destination target path for COPY/MOVE/RENAME")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Operation parameters (content, encoding, recursive, overwrite, etc.)")
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


class FileOperationResult(BaseModel):
    """Normalized result outcome of an executed filesystem operation."""

    operation_id: str = Field(..., description="Target operation ID")
    operation_type: FileOperationType = Field(..., description="Executed operation type")
    status: FileOperationStatus = Field(..., description="Operation outcome status")
    source: str = Field(..., description="Source path")
    destination: str | None = Field(default=None, description="Destination path if applicable")
    observed_state: dict[str, Any] = Field(default_factory=dict, description="Observed state parameters after execution")
    duration: float = Field(default=0.0, description="Execution duration in seconds")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Result timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class FileOperationFailure(BaseModel):
    """Structured failure representation for a failed filesystem operation."""

    operation_id: str = Field(..., description="Associated operation ID")
    operation_type: FileOperationType = Field(..., description="Associated operation type")
    reason: FileFailureReason = Field(..., description="Structured failure category")
    message: str = Field(..., description="Human-readable failure summary")
    details: dict[str, Any] = Field(default_factory=dict, description="Diagnostic failure details")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Failure timestamp"
    )


class FileOperation(BaseModel):
    """Full lifecycle model for a filesystem operation."""

    operation_id: str = Field(
        default_factory=lambda: f"fop_{uuid.uuid4().hex[:12]}",
        description="Unique operation ID",
    )
    request: FileOperationRequest = Field(..., description="Underlying operation request")
    status: FileOperationStatus = Field(default=FileOperationStatus.CREATED, description="Lifecycle status")
    result: FileOperationResult | None = Field(default=None, description="Operation result if completed")
    failure: FileOperationFailure | None = Field(default=None, description="Failure record if failed")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
