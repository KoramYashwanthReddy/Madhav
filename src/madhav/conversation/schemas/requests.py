"""API request DTO models for Conversation Engine endpoints."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CreateConversationRequest(BaseModel):
    """API payload for creating a new conversation."""

    title: str | None = Field(default=None, description="Optional conversation title")
    model_reference: str | None = Field(
        default=None, description="Optional model identifier reference"
    )
    auto_title_enabled: bool = Field(
        default=True, description="Toggle auto title generation on first turn"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Safe metadata key-value attributes"
    )


class UpdateConversationRequest(BaseModel):
    """API payload for updating conversation settings or metadata."""

    title: str | None = Field(default=None, description="Updated conversation title")
    model_reference: str | None = Field(
        default=None, description="Updated model identifier reference"
    )
    auto_title_enabled: bool | None = Field(default=None, description="Updated auto title flag")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Updated safe metadata key-value attributes"
    )


class UpdateTitleRequest(BaseModel):
    """API payload for explicit conversation title update."""

    title: str = Field(description="New title for the conversation")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Conversation title cannot be empty or whitespace-only.")
        return v.strip()


class SendMessageRequest(BaseModel):
    """API payload for sending a user message / executing a conversation turn."""

    content: str = Field(description="User message text content")
    client_message_id: str | None = Field(
        default=None, description="Optional unique client idempotent key"
    )
    model_override: str | None = Field(
        default=None, description="Optional model reference override for this turn"
    )

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure message content is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty or whitespace-only.")
        return v.strip()
