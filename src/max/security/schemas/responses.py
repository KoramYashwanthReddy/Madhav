"""Pydantic API response schemas for Module 15 — Permission & Security."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.approval import ApprovalRequest
from max.security.domain.audit import SecurityEvent, SecurityViolation
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.decision import PermissionDecision
from max.security.domain.emergency import EmergencyBlock, SecurityModeState
from max.security.domain.enums import (
    ApprovalStatus,
    DecisionReason,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    PermissionGrantType,
    PermissionScope,
    RiskLevel,
    SecurityEventType,
    SecurityMode,
    SecurityViolationType,
)
from max.security.domain.grant import PermissionGrant
from max.security.domain.permission import PermissionPolicy


class PermissionDecisionResponse(BaseModel):
    """API response model for permission check outcome."""

    decision_id: str = Field(..., description="Unique decision ID")
    request_id: str = Field(..., description="Associated request ID")
    status: PermissionDecisionStatus = Field(..., description="Decision status outcome")
    effect: PermissionEffect = Field(..., description="Evaluated effect outcome")
    reason: DecisionReason = Field(..., description="Structured rationale code")
    message: str = Field(..., description="Human-readable decision rationale")
    policy_id: str | None = Field(default=None, description="Matching policy ID")
    rule_id: str | None = Field(default=None, description="Matching rule ID")
    approval_required: bool = Field(default=False, description="Whether human approval is required")
    approval_request_id: str | None = Field(
        default=None, description="Generated approval request ID if required"
    )
    decided_at: datetime = Field(..., description="Decision timestamp")
    policy_version: int = Field(default=1, description="Active policy version")
    authorized_token: AuthorizedExecutionRequest | None = Field(
        default=None, description="Execution boundary authorization token if allowed"
    )

    @classmethod
    def from_domain(
        cls, decision: PermissionDecision, token: AuthorizedExecutionRequest | None = None
    ) -> "PermissionDecisionResponse":
        return cls(
            decision_id=decision.decision_id,
            request_id=decision.request_id,
            status=decision.status,
            effect=decision.effect,
            reason=decision.reason,
            message=decision.message,
            policy_id=decision.policy_id,
            rule_id=decision.rule_id,
            approval_required=decision.approval_required,
            approval_request_id=decision.approval_request_id,
            decided_at=decision.decided_at,
            policy_version=decision.policy_version,
            authorized_token=token,
        )


class PolicyResponse(BaseModel):
    """API response for a permission policy."""

    policy_id: str = Field(..., description="Unique policy ID")
    name: str = Field(..., description="Policy name")
    description: str | None = Field(default=None, description="Policy summary")
    priority: int = Field(..., description="Policy priority")
    enabled: bool = Field(..., description="Enabled status")
    scope: PermissionScope = Field(..., description="Policy scope")
    owner_id: str = Field(..., description="Owner boundary ID")
    version: int = Field(..., description="Policy version number")
    rule_count: int = Field(..., description="Number of rules")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @classmethod
    def from_domain(cls, policy: PermissionPolicy) -> "PolicyResponse":
        return cls(
            policy_id=policy.policy_id,
            name=policy.name,
            description=policy.description,
            priority=policy.priority,
            enabled=policy.enabled,
            scope=policy.scope,
            owner_id=policy.owner_id,
            version=policy.version,
            rule_count=len(policy.rules),
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )


class ApprovalRequestResponse(BaseModel):
    """API response for a human approval request."""

    approval_id: str = Field(..., description="Approval request ID")
    permission_request_id: str = Field(..., description="Associated permission request ID")
    title: str = Field(..., description="Approval title")
    explanation: str = Field(..., description="Human explanation")
    risk_level: RiskLevel = Field(..., description="Action risk level")
    requested_action: PermissionAction = Field(..., description="Requested action")
    requested_resource_id: str = Field(..., description="Target resource ID")
    owner_id: str = Field(..., description="Owner ID")
    status: ApprovalStatus = Field(..., description="Approval status")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    decided_at: datetime | None = Field(default=None, description="Decision timestamp")
    decided_by: str | None = Field(default=None, description="User who decided")
    decision_reason: str | None = Field(default=None, description="User decision rationale")

    @classmethod
    def from_domain(cls, approval: ApprovalRequest) -> "ApprovalRequestResponse":
        return cls(
            approval_id=approval.approval_id,
            permission_request_id=approval.permission_request_id,
            title=approval.title,
            explanation=approval.explanation,
            risk_level=approval.risk_level,
            requested_action=approval.requested_action,
            requested_resource_id=approval.requested_resource.resource_id,
            owner_id=approval.owner_id,
            status=approval.status,
            expires_at=approval.expires_at,
            created_at=approval.created_at,
            decided_at=approval.decided_at,
            decided_by=approval.decided_by,
            decision_reason=approval.decision_reason,
        )


class PermissionGrantResponse(BaseModel):
    """API response for a permission grant."""

    grant_id: str = Field(..., description="Grant ID")
    grant_type: PermissionGrantType = Field(..., description="Grant type")
    scope: PermissionScope = Field(..., description="Grant scope")
    owner_id: str = Field(..., description="Owner ID")
    is_active: bool = Field(..., description="Whether active")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime | None = Field(default=None, description="Expiration timestamp")

    @classmethod
    def from_domain(cls, grant: PermissionGrant) -> "PermissionGrantResponse":
        return cls(
            grant_id=grant.grant_id,
            grant_type=grant.grant_type,
            scope=grant.scope,
            owner_id=grant.owner_id,
            is_active=grant.is_active,
            created_at=grant.created_at,
            expires_at=grant.expires_at,
        )


class SecurityModeResponse(BaseModel):
    """API response for security operational mode state."""

    mode: SecurityMode = Field(..., description="Active security mode")
    changed_at: datetime = Field(..., description="Last mode change timestamp")
    changed_by: str = Field(..., description="User/system responsible")
    reason: str = Field(..., description="Change rationale")

    @classmethod
    def from_domain(cls, state: SecurityModeState) -> "SecurityModeResponse":
        return cls(
            mode=state.mode,
            changed_at=state.changed_at,
            changed_by=state.changed_by,
            reason=state.reason,
        )


class EmergencyBlockResponse(BaseModel):
    """API response for emergency kill-switch block status."""

    enabled: bool = Field(..., description="Emergency block active state")
    reason: str = Field(..., description="Activation justification")
    activated_at: datetime | None = Field(default=None, description="Activation timestamp")
    activated_by: str | None = Field(default=None, description="User who activated")

    @classmethod
    def from_domain(cls, block: EmergencyBlock) -> "EmergencyBlockResponse":
        return cls(
            enabled=block.enabled,
            reason=block.reason,
            activated_at=block.activated_at,
            activated_by=block.activated_by,
        )


class SecurityEventResponse(BaseModel):
    """API response for a security audit event."""

    event_id: str = Field(..., description="Event ID")
    event_type: SecurityEventType = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    owner_id: str = Field(..., description="Owner ID")
    summary: str = Field(..., description="Event summary")

    @classmethod
    def from_domain(cls, event: SecurityEvent) -> "SecurityEventResponse":
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            owner_id=event.owner_id,
            summary=event.summary,
        )


class SecurityViolationResponse(BaseModel):
    """API response for a security violation record."""

    violation_id: str = Field(..., description="Violation ID")
    violation_type: SecurityViolationType = Field(..., description="Violation type")
    timestamp: datetime = Field(..., description="Violation timestamp")
    owner_id: str = Field(..., description="Owner ID")
    summary: str = Field(..., description="Violation summary")

    @classmethod
    def from_domain(cls, violation: SecurityViolation) -> "SecurityViolationResponse":
        return cls(
            violation_id=violation.violation_id,
            violation_type=violation.violation_type,
            timestamp=violation.timestamp,
            owner_id=violation.owner_id,
            summary=violation.summary,
        )


class PaginatedSecurityResponse(BaseModel):
    """Generic paginated list wrapper for security responses."""

    items: list[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Page limit")
    offset: int = Field(..., description="Page offset")
