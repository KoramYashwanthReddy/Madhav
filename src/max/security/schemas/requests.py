"""Pydantic API request schemas for Module 15 — Permission & Security."""

from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import (
    ApprovalStatus,
    PermissionAction,
    PermissionEffect,
    PermissionGrantType,
    PermissionScope,
    PermissionSubjectType,
    ResourceSensitivity,
    RiskLevel,
    SecurityMode,
)


class PermissionSubjectPayload(BaseModel):
    """Subject specification in request payload."""

    subject_type: PermissionSubjectType = Field(
        default=PermissionSubjectType.USER, description="Subject category"
    )
    subject_id: str = Field(..., description="Unique subject ID")
    name: str | None = Field(default=None, description="Subject display name")


class PermissionResourcePayload(BaseModel):
    """Resource specification in request payload."""

    resource_type: str = Field(
        ..., description="Resource classification (FILE, TERMINAL, BROWSER, etc.)"
    )
    resource_id: str = Field(..., description="Target resource key or path")
    location: str | None = Field(default=None, description="Resource path URI or domain")
    owner_id: str = Field(default="default_owner", description="Resource owner boundary ID")
    sensitivity: ResourceSensitivity = Field(
        default=ResourceSensitivity.NORMAL, description="Data sensitivity level"
    )


class PermissionCheckRequest(BaseModel):
    """API request payload for evaluating action permissions."""

    subject: PermissionSubjectPayload = Field(..., description="Requesting subject payload")
    tool_reference: str | None = Field(default=None, description="Requested tool reference ID/name")
    action: PermissionAction = Field(..., description="Requested permission action")
    resource: PermissionResourcePayload = Field(..., description="Target resource payload")
    owner_id: str = Field(default="default_owner", description="Owner boundary identifier")
    agent_id: str | None = Field(default=None, description="Agent ID reference")
    agent_run_id: str | None = Field(default=None, description="Agent run ID reference")
    task_id: str | None = Field(default=None, description="Task ID reference")
    plan_id: str | None = Field(default=None, description="Plan ID reference")
    conversation_id: str | None = Field(default=None, description="Conversation ID reference")
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Inherent risk level")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Action parameter arguments"
    )


class PermissionConditionPayload(BaseModel):
    """Rule condition in policy create payload."""

    field: str = Field(..., description="Target property field")
    operator: str = Field(..., description="Comparison operator ('EQUALS', 'MATCHES_PATH', etc.)")
    value: Any = Field(..., description="Comparison target value")


class PermissionRulePayload(BaseModel):
    """Rule definition in policy create payload."""

    effect: PermissionEffect = Field(..., description="Rule outcome effect")
    priority: int = Field(default=100, description="Rule priority rank")
    reason: str = Field(default="Policy rule match", description="Rule justification rationale")
    subject_conditions: list[PermissionConditionPayload] = Field(default_factory=list)
    action_conditions: list[PermissionConditionPayload] = Field(default_factory=list)
    resource_conditions: list[PermissionConditionPayload] = Field(default_factory=list)
    tool_conditions: list[PermissionConditionPayload] = Field(default_factory=list)
    time_conditions: list[PermissionConditionPayload] = Field(default_factory=list)


class PolicyCreateRequest(BaseModel):
    """API request payload for creating a permission policy."""

    name: str = Field(..., description="Policy name")
    description: str | None = Field(default=None, description="Policy description")
    priority: int = Field(default=100, description="Policy precedence priority")
    enabled: bool = Field(default=True, description="Whether policy is active")
    rules: list[PermissionRulePayload] = Field(default_factory=list, description="Policy rules")
    scope: PermissionScope = Field(
        default=PermissionScope.GLOBAL, description="Policy applicability scope"
    )
    owner_id: str = Field(default="default_owner", description="Owner boundary ID")


class PolicyUpdateRequest(BaseModel):
    """API request payload for updating a permission policy."""

    name: str | None = Field(default=None, description="Updated policy name")
    description: str | None = Field(default=None, description="Updated description")
    priority: int | None = Field(default=None, description="Updated priority")
    enabled: bool | None = Field(default=None, description="Updated enabled state")
    rules: list[PermissionRulePayload] | None = Field(default=None, description="Updated rules")


class ApprovalDecisionRequest(BaseModel):
    """API request payload for resolving a human approval request."""

    status: ApprovalStatus = Field(
        ..., description="Approval status decision (APPROVED, DENIED, CANCELLED)"
    )
    decided_by: str = Field(..., description="User submitting the decision")
    reason: str | None = Field(default=None, description="Decision justification rationale")


class PermissionGrantRequest(BaseModel):
    """API request payload for creating a permission grant."""

    subject: PermissionSubjectPayload = Field(..., description="Target subject payload")
    action: PermissionAction = Field(..., description="Granted permission action")
    resource: PermissionResourcePayload = Field(..., description="Target resource payload")
    grant_type: PermissionGrantType = Field(
        default=PermissionGrantType.ONE_TIME, description="Grant duration classification"
    )
    scope: PermissionScope = Field(
        default=PermissionScope.EXACT_RESOURCE, description="Granted scope"
    )
    owner_id: str = Field(default="default_owner", description="Grantor owner ID")
    duration_seconds: float | None = Field(
        default=3600.0, description="Grant validity duration in seconds"
    )


class SecurityModeRequest(BaseModel):
    """API request payload for setting security operational mode."""

    mode: SecurityMode = Field(
        ..., description="Target security mode ('NORMAL', 'RESTRICTED', 'LOCKDOWN', 'MAINTENANCE')"
    )
    changed_by: str = Field(..., description="User identity requesting the change")
    reason: str = Field(default="", description="Justification for mode change")


class EmergencyBlockRequest(BaseModel):
    """API request payload for emergency kill-switch activation/deactivation."""

    activated_by: str = Field(..., description="User identity triggering the emergency change")
    reason: str = Field(default="", description="Reason for emergency block change")
