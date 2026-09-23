"""Domain model for permission grants."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionAction, PermissionGrantType, PermissionScope
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


class PermissionGrant(BaseModel):
    """Temporary or persistent permission grant issued by an owner or policy."""

    grant_id: str = Field(
        default_factory=lambda: f"grant_{uuid.uuid4().hex[:12]}",
        description="Unique grant identifier",
    )
    subject: PermissionSubject = Field(..., description="Target subject receiving the grant")
    action: PermissionAction = Field(..., description="Target granted action")
    resource: PermissionResource = Field(..., description="Target resource specification")
    scope: PermissionScope = Field(
        default=PermissionScope.EXACT_RESOURCE, description="Granted scope boundary"
    )
    grant_type: PermissionGrantType = Field(
        default=PermissionGrantType.ONE_TIME, description="Grant duration type"
    )
    owner_id: str = Field(..., description="Grantor owner identity")
    used_count: int = Field(default=0, description="Number of times ONE_TIME grant was consumed")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Grant creation timestamp"
    )
    expires_at: datetime | None = Field(default=None, description="Grant expiration timestamp")
    revoked_at: datetime | None = Field(default=None, description="Revocation timestamp if revoked")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")

    @property
    def is_active(self) -> bool:
        """Check if grant is currently active and unexpired."""
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.now(UTC) > self.expires_at:
            return False
        if self.grant_type == PermissionGrantType.ONE_TIME and self.used_count >= 1:
            return False
        return True
