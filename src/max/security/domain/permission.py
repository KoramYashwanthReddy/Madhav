"""Domain models for permissions, policies, and policy rules."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionAction, PermissionEffect, PermissionScope, RiskLevel
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


class PermissionCondition(BaseModel):
    """Evaluation condition for a policy rule."""

    field: str = Field(
        ..., description="Target property path (e.g. 'resource.location', 'subject.subject_id')"
    )
    operator: str = Field(
        ...,
        description="Condition operator ('EQUALS', 'NOT_EQUALS', 'IN', 'CONTAINS', 'STARTS_WITH', 'MATCHES_PATH', 'MATCHES_DOMAIN')",
    )
    value: Any = Field(..., description="Target comparison value")


class PermissionRule(BaseModel):
    """Deterministic rule within a permission policy."""

    rule_id: str = Field(
        default_factory=lambda: f"rule_{uuid.uuid4().hex[:12]}",
        description="Unique rule identifier",
    )
    effect: PermissionEffect = Field(
        ..., description="Outcome if rule matches (ALLOW, DENY, REQUIRE_APPROVAL)"
    )
    priority: int = Field(
        default=100, description="Rule precedence rank (higher numerical value = higher priority)"
    )
    reason: str = Field(default="Policy rule match", description="Rationale for rule effect")
    subject_conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Subject match conditions"
    )
    action_conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Action match conditions"
    )
    resource_conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Resource match conditions"
    )
    tool_conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Tool match conditions"
    )
    time_conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Time/expiration match conditions"
    )


class PermissionPolicy(BaseModel):
    """Named collection of policy rules governing permission decisions."""

    policy_id: str = Field(
        default_factory=lambda: f"pol_{uuid.uuid4().hex[:12]}",
        description="Unique policy identifier",
    )
    name: str = Field(..., description="Human-readable policy name")
    description: str | None = Field(default=None, description="Policy summary description")
    priority: int = Field(default=100, description="Policy precedence priority")
    enabled: bool = Field(default=True, description="Whether policy is active")
    rules: list[PermissionRule] = Field(default_factory=list, description="Ordered rules")
    scope: PermissionScope = Field(
        default=PermissionScope.GLOBAL, description="Target applicability scope"
    )
    owner_id: str = Field(..., description="Owner boundary identity")
    version: int = Field(default=1, description="Policy version number")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )


class Permission(BaseModel):
    """Explicit permission statement model."""

    permission_id: str = Field(
        default_factory=lambda: f"perm_{uuid.uuid4().hex[:12]}",
        description="Unique permission identifier",
    )
    subject: PermissionSubject = Field(..., description="Target subject")
    action: PermissionAction = Field(..., description="Target action")
    resource: PermissionResource = Field(..., description="Target resource")
    scope: PermissionScope = Field(
        default=PermissionScope.EXACT_RESOURCE, description="Permission boundary scope"
    )
    effect: PermissionEffect = Field(default=PermissionEffect.ALLOW, description="Granted effect")
    conditions: list[PermissionCondition] = Field(
        default_factory=list, description="Active conditions"
    )
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Associated risk level")
    approval_requirement: bool = Field(default=False, description="Whether approval is mandatory")
    valid_from: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Validity start timestamp"
    )
    expires_at: datetime | None = Field(
        default=None, description="Expiration timestamp (None = perpetual)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")
