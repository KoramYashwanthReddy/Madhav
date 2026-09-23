"""Domain models for security audit events and security violations."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionAction, SecurityEventType, SecurityViolationType
from max.security.domain.subject import SecurityPrincipal


class SecurityEvent(BaseModel):
    """Immutable security audit log record."""

    event_id: str = Field(
        default_factory=lambda: f"sevt_{uuid.uuid4().hex[:12]}",
        description="Unique event identifier",
    )
    event_type: SecurityEventType = Field(..., description="Categorization of security event")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event creation timestamp"
    )
    principal: SecurityPrincipal | None = Field(
        default=None, description="Associated security principal"
    )
    owner_id: str = Field(..., description="Owner boundary identifier")
    tool_id: str | None = Field(default=None, description="Tool identifier if tool-related")
    action: PermissionAction | None = Field(
        default=None, description="Permission action if applicable"
    )
    resource_id: str | None = Field(default=None, description="Resource identifier if applicable")
    request_id: str | None = Field(default=None, description="Permission request ID")
    decision_id: str | None = Field(default=None, description="Permission decision ID")
    summary: str = Field(..., description="Human-readable event summary")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Structured event payload attributes"
    )


class SecurityViolation(BaseModel):
    """Security policy or boundary violation record."""

    violation_id: str = Field(
        default_factory=lambda: f"svio_{uuid.uuid4().hex[:12]}",
        description="Unique violation identifier",
    )
    violation_type: SecurityViolationType = Field(..., description="Classification of violation")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Violation timestamp"
    )
    principal: SecurityPrincipal | None = Field(
        default=None, description="Associated security principal"
    )
    owner_id: str = Field(..., description="Owner boundary identifier")
    tool_id: str | None = Field(default=None, description="Tool identifier if tool-related")
    summary: str = Field(..., description="Violation description")
    details: dict[str, Any] = Field(default_factory=dict, description="Detailed diagnostic context")
