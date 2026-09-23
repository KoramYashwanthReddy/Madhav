"""Message domain model."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from madhav.conversation.domain.enums import MessageRole, MessageStatus


class Message(BaseModel):
    """Domain entity representing an individual message in a conversation thread."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    conversation_id: UUID = Field(description="Parent conversation identifier")
    sequence: int = Field(description="Monotonically increasing chronological sequence number")
    role: MessageRole = Field(description="Role of message sender")
    content: str = Field(description="Textual message content")
    status: MessageStatus = Field(
        default=MessageStatus.COMPLETED, description="Message processing state"
    )
    client_message_id: str | None = Field(
        default=None, description="Optional client-provided unique idempotent key"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of message creation",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of last message modification",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe execution metadata"
    )
