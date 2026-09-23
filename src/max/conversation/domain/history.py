"""Conversation history aggregate response model."""

from pydantic import BaseModel, Field

from max.conversation.domain.conversation import Conversation
from max.conversation.domain.message import Message


class ConversationHistory(BaseModel):
    """Paginated conversation message history container."""

    conversation: Conversation = Field(description="Parent conversation aggregate")
    messages: list[Message] = Field(description="Ordered list of conversation messages")
    total_messages: int = Field(description="Total message count in conversation")
    limit: int = Field(description="Pagination page size limit")
    offset: int = Field(description="Pagination offset index")
    has_more: bool = Field(
        description="Indicates whether more messages exist beyond current window"
    )
