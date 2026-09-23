"""API response DTO models for Conversation Engine endpoints."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from max.conversation.domain.conversation import Conversation
from max.conversation.domain.history import ConversationHistory
from max.conversation.domain.message import Message
from max.conversation.domain.summary import ConversationSummary
from max.conversation.services.turn_service import TurnResult


class ConversationResponse(BaseModel):
    """API DTO representing a conversation object."""

    conversation_id: UUID = Field(description="Unique conversation identifier")
    owner_id: str = Field(description="Owner identity identifier")
    title: str | None = Field(default=None, description="Conversation title")
    status: str = Field(description="Lifecycle status string")
    settings: dict[str, Any] = Field(description="Conversation settings dict")
    message_count: int = Field(description="Total message count")
    created_at: str = Field(description="Creation UTC ISO timestamp")
    updated_at: str = Field(description="Last update UTC ISO timestamp")
    last_message_at: str | None = Field(default=None, description="Last message UTC ISO timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe metadata")

    @classmethod
    def from_domain(cls, conv: Conversation) -> "ConversationResponse":
        """Construct DTO from domain model."""
        return cls(
            conversation_id=conv.conversation_id,
            owner_id=conv.owner_id,
            title=conv.title,
            status=conv.status.value,
            settings=conv.settings.model_dump(),
            message_count=conv.message_count,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
            last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
            metadata=conv.metadata,
        )


class MessageResponse(BaseModel):
    """API DTO representing an individual message object."""

    message_id: UUID = Field(description="Unique message identifier")
    conversation_id: UUID = Field(description="Parent conversation identifier")
    sequence: int = Field(description="Chronological sequence number")
    role: str = Field(description="Sender role string ('user', 'assistant', etc.)")
    content: str = Field(description="Textual content")
    status: str = Field(description="Processing status string")
    client_message_id: str | None = Field(default=None, description="Idempotent client key")
    created_at: str = Field(description="Creation UTC ISO timestamp")
    updated_at: str = Field(description="Update UTC ISO timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Execution metadata")

    @classmethod
    def from_domain(cls, msg: Message) -> "MessageResponse":
        """Construct DTO from domain model."""
        return cls(
            message_id=msg.message_id,
            conversation_id=msg.conversation_id,
            sequence=msg.sequence,
            role=msg.role.value,
            content=msg.content,
            status=msg.status.value,
            client_message_id=msg.client_message_id,
            created_at=msg.created_at.isoformat(),
            updated_at=msg.updated_at.isoformat(),
            metadata=msg.metadata,
        )


class ConversationSummaryResponse(BaseModel):
    """API DTO representing a lightweight conversation summary."""

    conversation_id: UUID = Field(description="Unique conversation identifier")
    owner_id: str = Field(description="Owner identity identifier")
    title: str | None = Field(default=None, description="Conversation title")
    status: str = Field(description="Lifecycle status string")
    created_at: str = Field(description="Creation UTC ISO timestamp")
    updated_at: str = Field(description="Last update UTC ISO timestamp")
    last_message_at: str | None = Field(default=None, description="Last message UTC ISO timestamp")
    message_count: int = Field(description="Total message count")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe metadata")

    @classmethod
    def from_domain(cls, summary: ConversationSummary) -> "ConversationSummaryResponse":
        """Construct DTO from domain summary model."""
        return cls(
            conversation_id=summary.conversation_id,
            owner_id=summary.owner_id,
            title=summary.title,
            status=summary.status.value,
            created_at=summary.created_at.isoformat(),
            updated_at=summary.updated_at.isoformat(),
            last_message_at=summary.last_message_at.isoformat()
            if summary.last_message_at
            else None,
            message_count=summary.message_count,
            metadata=summary.metadata,
        )


class ConversationListResponse(BaseModel):
    """Paginated conversation list response object."""

    conversations: list[ConversationSummaryResponse] = Field(
        description="List of conversation summaries"
    )
    total: int = Field(description="Total matching count")
    limit: int = Field(description="Page limit")
    offset: int = Field(description="Page offset")
    has_more: bool = Field(description="Flag indicating additional items exist")


class ConversationHistoryResponse(BaseModel):
    """Paginated message history response object."""

    conversation: ConversationResponse = Field(description="Parent conversation")
    messages: list[MessageResponse] = Field(description="List of message objects")
    total_messages: int = Field(description="Total message count")
    limit: int = Field(description="Page limit")
    offset: int = Field(description="Page offset")
    has_more: bool = Field(description="Flag indicating additional messages exist")

    @classmethod
    def from_domain(cls, history: ConversationHistory) -> "ConversationHistoryResponse":
        """Construct DTO from domain history model."""
        return cls(
            conversation=ConversationResponse.from_domain(history.conversation),
            messages=[MessageResponse.from_domain(m) for m in history.messages],
            total_messages=history.total_messages,
            limit=history.limit,
            offset=history.offset,
            has_more=history.has_more,
        )


class TurnResponse(BaseModel):
    """API DTO returned upon executing a conversational turn."""

    conversation: ConversationResponse = Field(description="Updated conversation state")
    user_message: MessageResponse = Field(description="Persisted user message")
    assistant_message: MessageResponse = Field(description="Persisted assistant response")
    usage: dict[str, Any] | None = Field(default=None, description="AI token usage details")
    execution_time_ms: float | None = Field(default=None, description="Execution duration in ms")

    @classmethod
    def from_domain(cls, result: TurnResult) -> "TurnResponse":
        """Construct DTO from domain TurnResult."""
        return cls(
            conversation=ConversationResponse.from_domain(result.conversation),
            user_message=MessageResponse.from_domain(result.user_message),
            assistant_message=MessageResponse.from_domain(result.assistant_message),
            usage=result.usage.model_dump() if result.usage else None,
            execution_time_ms=result.execution_time_ms,
        )
