"""Conversation summary model for listing endpoints."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from max.conversation.domain.enums import ConversationStatus


class ConversationSummary(BaseModel):
    """Lightweight projection model of a conversation without message payload."""

    conversation_id: UUID = Field(description="Unique conversation identifier")
    owner_id: str = Field(description="Owner identity identifier")
    title: str | None = Field(default=None, description="Conversation title")
    status: ConversationStatus = Field(description="Lifecycle status")
    created_at: datetime = Field(description="Time of creation")
    updated_at: datetime = Field(description="Time of last update")
    last_message_at: datetime | None = Field(default=None, description="Time of last message")
    message_count: int = Field(description="Total message count")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe metadata")
