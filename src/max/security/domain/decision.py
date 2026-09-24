"""Domain models for security context, requests, and decisions."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import (
    DecisionReason,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    RiskLevel,
    SecurityMode,
)
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject, SecurityPrincipal


class SecurityContext(BaseModel):
    """Unified security context capturing request state during evaluation."""

    principal: SecurityPrincipal = Field(..., description="Security principal identity")
    owner_id: str = Field(..., description="Target resource/system owner ID")
    agent_id: str | None = Field(default=None, description="Requesting agent ID if applicable")
    agent_run_id: str | None = Field(default=None, description="Agent run ID if applicable")
    tool_id: str | None = Field(default=None, description="Requested tool ID if applicable")
    tool_version: str | None = Field(
        default=None, description="Requested tool version if applicable"
    )
    action: PermissionAction = Field(..., description="Requested permission action")
    resource: PermissionResource = Field(..., description="Target permission resource")
    task_id: str | None = Field(default=None, description="Task context reference")
    plan_id: str | None = Field(default=None, description="Plan context reference")
    plan_step_id: str | None = Field(default=None, description="Plan step reference")
    conversation_id: str | None = Field(default=None, description="Conversation context reference")
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM, description="Assessed action risk level"
    )
    security_mode: SecurityMode = Field(
        default=SecurityMode.NORMAL, description="Current system security mode"
    )
    emergency_block_active: bool = Field(
        default=False, description="Whether global emergency block is active"
    )
    policy_version: int = Field(default=1, description="Active policy version reference")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Tool / action argument parameters"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Context creation timestamp"
    )


class PermissionRequest(BaseModel):
    """Structured request to evaluate permission for an action."""

    request_id: str = Field(
        default_factory=lambda: f"preq_{uuid.uuid4().hex[:12]}",
        description="Unique request identifier",
    )
    subject: PermissionSubject = Field(..., description="Requesting subject")
    tool_reference: str | None = Field(default=None, description="Requested tool key or ID")
    action: PermissionAction = Field(..., description="Requested permission action")
    resource: PermissionResource = Field(..., description="Target resource description")
    owner_id: str = Field(..., description="Owner boundary identity")
    agent_id: str | None = Field(default=None, description="Agent identifier if agent-driven")
    agent_run_id: str | None = Field(
        default=None, description="Agent run identifier if agent-driven"
    )
    task_id: str | None = Field(default=None, description="Task reference identifier")
    plan_id: str | None = Field(default=None, description="Plan reference identifier")
    conversation_id: str | None = Field(
        default=None, description="Conversation reference identifier"
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM, description="Inherent action risk level"
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Target operation arguments"
    )
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Request creation timestamp"
    )
    expires_at: datetime | None = Field(
        default=None, description="Request validity expiry timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")


class PermissionDecision(BaseModel):
    """Deterministic outcome of a policy evaluation."""

    decision_id: str = Field(
        default_factory=lambda: f"dec_{uuid.uuid4().hex[:12]}",
        description="Unique decision identifier",
    )
    request_id: str = Field(..., description="Associated request identifier")
    status: PermissionDecisionStatus = Field(..., description="Overall decision status")
    effect: PermissionEffect = Field(..., description="Evaluated effect outcome")
    reason: DecisionReason = Field(..., description="Structured decision rationale code")
    message: str = Field(default="", description="Detailed human-readable explanation")
    policy_id: str | None = Field(default=None, description="Matching policy ID if applicable")
    rule_id: str | None = Field(default=None, description="Matching rule ID if applicable")
    approval_required: bool = Field(default=False, description="Whether human approval is required")
    approval_request_id: str | None = Field(
        default=None, description="Generated approval request ID if required"
    )
    decided_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Decision evaluation timestamp"
    )
    expires_at: datetime | None = Field(default=None, description="Decision validity expiration")
    policy_version: int = Field(default=1, description="Policy version at evaluation time")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Decision evaluation metadata"
    )

    @property
    def is_allowed(self) -> bool:
        return self.effect == PermissionEffect.ALLOW
