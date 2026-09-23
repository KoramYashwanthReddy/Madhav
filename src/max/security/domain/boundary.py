"""Execution boundary models and interfaces for future execution modules (16+)."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionAction
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


class AuthorizedExecutionRequest(BaseModel):
    """Authorization contract token passed to future execution modules (Modules 16+).

    Represents an action that has passed all permission, security mode, emergency block,
    and approval gates.
    """

    invocation_id: str = Field(
        default_factory=lambda: f"auth_inv_{uuid.uuid4().hex[:12]}",
        description="Unique authorized execution token identifier",
    )
    permission_decision_id: str = Field(
        ..., description="Target decision ID confirming authorization"
    )
    tool_reference: str | None = Field(default=None, description="Target tool ID or name")
    action: PermissionAction = Field(..., description="Authorized permission action")
    resource: PermissionResource = Field(..., description="Target authorized resource")
    subject: PermissionSubject = Field(..., description="Authorized subject")
    owner_id: str = Field(..., description="Resource owner boundary identity")
    authorization_expiry: datetime = Field(..., description="Authorization validity expiration")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Token issue timestamp"
    )
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Validated argument parameters"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Authorization metadata")

    @property
    def is_valid(self) -> bool:
        """Check if authorization token is unexpired."""
        return datetime.now(UTC) <= self.authorization_expiry
