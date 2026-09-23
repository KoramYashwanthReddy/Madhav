"""Abstract base repository protocol for Conversation Engine."""

from typing import Protocol
from uuid import UUID

from madhav.conversation.domain.conversation import Conversation
from madhav.conversation.domain.enums import ConversationStatus
from madhav.conversation.domain.message import Message


class ConversationRepository(Protocol):
    """Repository interface defining storage operations for conversations and messages."""

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Persist a new conversation aggregate."""
        ...

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        """Retrieve a conversation aggregate by ID, returns None if not found."""
        ...

    async def list_conversations(
        self,
        owner_id: str,
        status: ConversationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        """List conversations for an owner with optional status filter and pagination."""
        ...

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update metadata, title, settings, status, or timestamps of a conversation."""
        ...

    async def archive_conversation(self, conversation_id: UUID) -> Conversation:
        """Transition conversation state to ARCHIVED."""
        ...

    async def restore_conversation(self, conversation_id: UUID) -> Conversation:
        """Transition conversation state from ARCHIVED back to ACTIVE."""
        ...

    async def delete_conversation(self, conversation_id: UUID, soft_delete: bool = True) -> bool:
        """Delete conversation. If soft_delete is True, mark status as DELETED."""
        ...

    async def create_message(self, message: Message) -> Message:
        """Persist a message entity in a conversation."""
        ...

    async def get_message(self, message_id: UUID) -> Message | None:
        """Retrieve a message entity by ID."""
        ...

    async def get_message_by_client_id(
        self, conversation_id: UUID, client_message_id: str
    ) -> Message | None:
        """Retrieve a message by client_message_id for idempotency verification."""
        ...

    async def list_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
        asc: bool = True,
    ) -> tuple[list[Message], int]:
        """List messages for a conversation ordered by sequence."""
        ...

    async def get_latest_messages(self, conversation_id: UUID, limit: int = 100) -> list[Message]:
        """Retrieve the N most recent messages for a conversation in chronological order."""
        ...

    async def get_next_sequence(self, conversation_id: UUID) -> int:
        """Safely compute the next sequence number for a message in a conversation."""
        ...
