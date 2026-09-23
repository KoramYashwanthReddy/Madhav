"""Domain models for security actions."""

from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionAction, RiskLevel


class ActionDefinition(BaseModel):
    """Explicit action definition with risk and requirements."""

    action: PermissionAction = Field(..., description="Canonical permission action enum")
    description: str | None = Field(default=None, description="Human-readable action description")
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM, description="Inherent action risk level"
    )
    requires_approval_by_default: bool = Field(
        default=False, description="Whether action defaults to requiring user approval"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Action classification metadata"
    )
