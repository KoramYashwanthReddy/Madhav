"""Conversation settings domain model."""

from typing import Any

from pydantic import BaseModel, Field


class ConversationSettingsModel(BaseModel):
    """Configuration settings specific to an individual conversation."""

    model_reference: str | None = Field(
        default=None, description="Optional model identifier override for this conversation"
    )
    context_policy: str | None = Field(
        default=None, description="Optional context selection policy override for this conversation"
    )
    response_preferences: dict[str, Any] = Field(
        default_factory=dict, description="Custom generation preferences (e.g. temperature, tone)"
    )
    auto_title_enabled: bool = Field(
        default=True, description="Toggle automatic title generation on first conversation turn"
    )
