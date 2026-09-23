"""Domain models for emergency kill-switch and security mode state."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import SecurityMode


class EmergencyBlock(BaseModel):
    """Global emergency block / kill-switch state representation."""

    enabled: bool = Field(default=False, description="Whether emergency block is active")
    reason: str = Field(default="", description="Reason for emergency block activation")
    activated_at: datetime | None = Field(default=None, description="Activation timestamp")
    activated_by: str | None = Field(
        default=None, description="User identity who activated the kill-switch"
    )
    expires_at: datetime | None = Field(
        default=None, description="Automatic deactivation timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class SecurityModeState(BaseModel):
    """System security mode state representation."""

    mode: SecurityMode = Field(
        default=SecurityMode.NORMAL, description="Active security operational mode"
    )
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last mode change timestamp"
    )
    changed_by: str = Field(default="SYSTEM", description="Identity responsible for mode change")
    reason: str = Field(
        default="Initial default security mode", description="Justification for mode change"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")
