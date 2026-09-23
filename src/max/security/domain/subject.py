"""Domain models for security subjects and principals."""

import uuid
from typing import Any

from pydantic import BaseModel, Field

from max.security.domain.enums import PermissionSubjectType


class PermissionSubject(BaseModel):
    """Subject identity requesting an action."""

    subject_type: PermissionSubjectType = Field(..., description="Subject category classification")
    subject_id: str = Field(..., description="Unique subject identifier (user_id, agent_id, etc.)")
    name: str | None = Field(default=None, description="Human-readable subject name")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional subject attributes"
    )


class SecurityPrincipal(BaseModel):
    """Security identity representation used during policy evaluation."""

    principal_id: str = Field(
        default_factory=lambda: f"prn_{uuid.uuid4().hex[:12]}",
        description="Unique principal identifier",
    )
    subject: PermissionSubject = Field(..., description="Underlying permission subject")
    owner_id: str = Field(..., description="Resource/System owner identity boundary")
    roles: list[str] = Field(default_factory=list, description="Assigned security roles")
    attributes: dict[str, Any] = Field(
        default_factory=dict, description="Contextual security attributes"
    )
