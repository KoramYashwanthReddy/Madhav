"""ConversationService application service facade for conversation management."""

import logging
from typing import Any
from uuid import UUID

from madhav.config.settings import get_settings
from madhav.conversation.domain.conversation import Conversation
from madhav.conversation.domain.enums import ConversationStatus
from madhav.conversation.domain.history import ConversationHistory
from madhav.conversation.domain.message import Message
from madhav.conversation.domain.settings import ConversationSettingsModel
from madhav.conversation.domain.summary import ConversationSummary
from madhav.conversation.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
    MessageValidationError,
)
from madhav.conversation.repositories.base import ConversationRepository
from madhav.conversation.repositories.memory import InMemoryConversationRepository
from madhav.conversation.services.title_generator import DeterministicTitleGenerator
from madhav.conversation.services.turn_service import ConversationTurnService, TurnResult

logger = logging.getLogger(__name__)


class ConversationService:
    """Service facade for managing conversations, messages, lifecycle, and turns."""

    def __init__(
        self,
        repository: ConversationRepository | None = None,
        turn_service: ConversationTurnService | None = None,
        title_generator: DeterministicTitleGenerator | None = None,
    ) -> None:
        self._repository = repository or InMemoryConversationRepository()
        self._title_generator = title_generator or DeterministicTitleGenerator()
        self._turn_service = turn_service or ConversationTurnService(
            repository=self._repository, title_generator=self._title_generator
        )
        self._cfg = get_settings().conversation

    @property
    def repository(self) -> ConversationRepository:
        """Access lower-level conversation repository."""
        return self._repository

    async def create_conversation(
        self,
        owner_id: str = "default_owner",
        title: str | None = None,
        settings: ConversationSettingsModel | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """Create a new conversation aggregate."""

        validated_title: str | None = None
        if title is not None:
            clean_title = title.strip()
            if clean_title:
                if len(clean_title) > self._cfg.max_title_characters:
                    clean_title = clean_title[: self._cfg.max_title_characters].rstrip()
                validated_title = clean_title

        conv = Conversation(
            owner_id=owner_id,
            title=validated_title,
            settings=settings or ConversationSettingsModel(),
            metadata=metadata or {},
        )
        created = await self._repository.create_conversation(conv)
        logger.info("Created conversation %s for owner %s", created.conversation_id, owner_id)
        return created

    async def get_conversation(self, conversation_id: UUID) -> Conversation:
        """Retrieve conversation aggregate, raising NotFound or Deleted errors."""
        conv = await self._repository.get_conversation(conversation_id)
        if conv is None or conv.status == ConversationStatus.DELETED:
            raise ConversationNotFoundError(
                f"Conversation {conversation_id} not found.",
                details={"conversation_id": str(conversation_id)},
            )
        return conv

    async def list_conversations(
        self,
        owner_id: str = "default_owner",
        status: ConversationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ConversationSummary], int]:
        """List conversations for an owner with pagination."""

        page_limit = min(
            limit if limit > 0 else self._cfg.default_page_size, self._cfg.max_page_size
        )
        page_offset = max(0, offset)

        convs, total = await self._repository.list_conversations(
            owner_id=owner_id, status=status, limit=page_limit, offset=page_offset
        )

        summaries = [
            ConversationSummary(
                conversation_id=c.conversation_id,
                owner_id=c.owner_id,
                title=c.title,
                status=c.status,
                created_at=c.created_at,
                updated_at=c.updated_at,
                last_message_at=c.last_message_at,
                message_count=c.message_count,
                metadata=c.metadata,
            )
            for c in convs
        ]
        return summaries, total

    async def update_conversation(
        self,
        conversation_id: UUID,
        title: str | None = None,
        settings: ConversationSettingsModel | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """Update conversation properties."""
        conv = await self.get_conversation(conversation_id)

        if title is not None:
            clean = title.strip()
            if not clean:
                raise MessageValidationError("Conversation title cannot be empty.")
            if len(clean) > self._cfg.max_title_characters:
                clean = clean[: self._cfg.max_title_characters].rstrip()
            conv.title = clean

        if settings is not None:
            conv.settings = settings

        if metadata is not None:
            conv.metadata.update(metadata)

        updated = await self._repository.update_conversation(conv)
        return updated

    async def update_title(self, conversation_id: UUID, title: str) -> Conversation:
        """Update title of an active conversation explicitly."""
        return await self.update_conversation(conversation_id, title=title)

    async def archive_conversation(self, conversation_id: UUID) -> Conversation:
        """Archive conversation."""
        await self.get_conversation(conversation_id)  # Validate existence
        archived = await self._repository.archive_conversation(conversation_id)
        logger.info("Archived conversation %s", conversation_id)
        return archived

    async def restore_conversation(self, conversation_id: UUID) -> Conversation:
        """Restore archived conversation back to ACTIVE."""
        # Retrieve raw conversation to check if deleted
        raw = await self._repository.get_conversation(conversation_id)
        if raw is None or raw.status == ConversationStatus.DELETED:
            raise ConversationNotFoundError(f"Conversation {conversation_id} not found.")
        restored = await self._repository.restore_conversation(conversation_id)
        logger.info("Restored conversation %s", conversation_id)
        return restored

    async def delete_conversation(self, conversation_id: UUID, soft_delete: bool = True) -> bool:
        """Delete conversation."""
        await self.get_conversation(conversation_id)  # Validate existence
        result = await self._repository.delete_conversation(
            conversation_id, soft_delete=soft_delete
        )
        logger.info("Deleted conversation %s (soft_delete=%s)", conversation_id, soft_delete)
        return result

    async def list_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
        asc: bool = True,
    ) -> ConversationHistory:
        """List message history for a conversation."""
        conv = await self.get_conversation(conversation_id)

        page_limit = min(
            limit if limit > 0 else self._cfg.default_page_size, self._cfg.max_page_size
        )
        page_offset = max(0, offset)

        msgs, total = await self._repository.list_messages(
            conversation_id=conversation_id, limit=page_limit, offset=page_offset, asc=asc
        )

        has_more = (page_offset + page_limit) < total

        return ConversationHistory(
            conversation=conv,
            messages=msgs,
            total_messages=total,
            limit=page_limit,
            offset=page_offset,
            has_more=has_more,
        )

    async def get_message(self, conversation_id: UUID, message_id: UUID) -> Message:
        """Retrieve individual message by ID."""
        await self.get_conversation(conversation_id)  # Validate conversation existence
        msg = await self._repository.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise MessageNotFoundError(
                f"Message {message_id} not found in conversation {conversation_id}.",
                details={"message_id": str(message_id), "conversation_id": str(conversation_id)},
            )
        return msg

    async def send_message(
        self,
        conversation_id: UUID,
        content: str,
        client_message_id: str | None = None,
        model_override: str | None = None,
        owner_id: str = "default_owner",
    ) -> TurnResult:
        """Execute a conversational turn via ConversationTurnService."""
        return await self._turn_service.execute_turn(
            conversation_id=conversation_id,
            user_content=content,
            client_message_id=client_message_id,
            model_override=model_override,
            owner_id=owner_id,
        )
