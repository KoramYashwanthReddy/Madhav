"""ContextRequest domain model representing an input context assembly request."""

import uuid
from typing import Any

from pydantic import BaseModel, Field, field_validator

from max.context.domain.budget import ContextBudget
from max.context.domain.policy import ContextPolicy
from max.identity.domain.context import IdentityContext


class ContextRequest(BaseModel):
    """Specification of an incoming context assembly request for AI model input preparation."""

    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique correlation identifier for context request",
    )
    user_request: str = Field(description="Primary prompt or command content submitted by user")
    identity_context: IdentityContext | None = Field(
        default=None, description="Optional Module 03 identity context snapshot"
    )
    model_reference: str | None = Field(
        default=None, description="Optional target model identifier (e.g. 'development-stub')"
    )
    policy: ContextPolicy | None = Field(
        default=None,
        description="Optional custom ContextPolicy (defaults to ContextPolicy.default())",
    )
    budget: ContextBudget | None = Field(
        default=None,
        description="Optional explicit ContextBudget (overrides model/config budget)",
    )
    source_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration options passed to registered context sources",
    )

    @field_validator("user_request")
    @classmethod
    def validate_user_request_not_empty(cls, v: str) -> str:
        """Ensure user request string is non-empty and stripped of outer whitespace."""
        if not v or not v.strip():
            raise ValueError("user_request cannot be empty or whitespace-only.")
        return v.strip()
