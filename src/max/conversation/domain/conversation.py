"""Conversation domain aggregate root model."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from max.conversation.domain.enums import ConversationStatus
from max.conversation.domain.settings import ConversationSettingsModel


class Conversation(BaseModel):
    """Domain aggregate representing a structured conversation session."""

    conversation_id: UUID = Field(
        default_factory=uuid4, description="Unique conversation identifier"
    )
    owner_id: str = Field(description="Identifier of identity owning this conversation")
    title: str | None = Field(default=None, description="Human-readable conversation title")
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE, description="Lifecycle status"
    )
    settings: ConversationSettingsModel = Field(
        default_factory=ConversationSettingsModel, description="Conversation settings"
    )
    message_count: int = Field(default=0, description="Total number of persisted messages")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of conversation creation",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of last conversation metadata or message modification",
    )
    last_message_at: datetime | None = Field(
        default=None, description="Time of most recent message addition"
    )
    deleted_at: datetime | None = Field(
        default=None, description="Time of soft deletion if applicable"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata key-values"
    )

    def is_active(self) -> bool:
        """Check if conversation is in ACTIVE state."""
        return self.status == ConversationStatus.ACTIVE

    def is_archived(self) -> bool:
        """Check if conversation is in ARCHIVED state."""
        return self.status == ConversationStatus.ARCHIVED

    def is_deleted(self) -> bool:
        """Check if conversation is in DELETED state."""
        return self.status == ConversationStatus.DELETED
