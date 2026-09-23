"""In-memory thread and async safe implementation of ConversationRepository."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID

from max.conversation.domain.conversation import Conversation
from max.conversation.domain.enums import ConversationStatus
from max.conversation.domain.message import Message
from max.conversation.exceptions import (
    ConversationArchivedError,
    ConversationDeletedError,
    ConversationNotFoundError,
    InvalidConversationStateError,
)
from max.conversation.repositories.base import ConversationRepository


class InMemoryConversationRepository(ConversationRepository):
    """Development in-memory repository implementing ConversationRepository.

    Thread and async safe with per-conversation sequence locks and full lifecycle validation.
    """

    def __init__(self) -> None:
        self._conversations: dict[UUID, Conversation] = {}
        self._messages: dict[UUID, list[Message]] = {}
        self._locks: dict[UUID, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_conv_lock(self, conversation_id: UUID) -> asyncio.Lock:
        async with self._global_lock:
            if conversation_id not in self._locks:
                self._locks[conversation_id] = asyncio.Lock()
            return self._locks[conversation_id]

    async def create_conversation(self, conversation: Conversation) -> Conversation:
        async with self._global_lock:
            conv_copy = conversation.model_copy(deep=True)
            self._conversations[conv_copy.conversation_id] = conv_copy
            self._messages[conv_copy.conversation_id] = []
            self._locks[conv_copy.conversation_id] = asyncio.Lock()
            return conv_copy.model_copy(deep=True)

    async def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        async with self._global_lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                return None
            return conv.model_copy(deep=True)

    async def list_conversations(
        self,
        owner_id: str,
        status: ConversationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Conversation], int]:
        async with self._global_lock:
            matching: list[Conversation] = []
            for conv in self._conversations.values():
                if conv.owner_id != owner_id:
                    continue
                if status is not None:
                    if conv.status != status:
                        continue
                else:
                    # By default exclude soft-deleted conversations
                    if conv.status == ConversationStatus.DELETED:
                        continue
                matching.append(conv)

            # Sort by updated_at descending
            matching.sort(key=lambda c: c.updated_at, reverse=True)
            total = len(matching)
            paginated = matching[offset : offset + limit]
            return [c.model_copy(deep=True) for c in paginated], total

    async def update_conversation(self, conversation: Conversation) -> Conversation:
        lock = await self._get_conv_lock(conversation.conversation_id)
        async with lock:
            if conversation.conversation_id not in self._conversations:
                raise ConversationNotFoundError(
                    f"Conversation {conversation.conversation_id} not found.",
                    details={"conversation_id": str(conversation.conversation_id)},
                )
            conv_copy = conversation.model_copy(deep=True)
            conv_copy.updated_at = datetime.now(UTC)
            self._conversations[conversation.conversation_id] = conv_copy
            return conv_copy.model_copy(deep=True)

    async def archive_conversation(self, conversation_id: UUID) -> Conversation:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.status == ConversationStatus.DELETED:
                raise ConversationDeletedError(
                    f"Cannot archive deleted conversation {conversation_id}.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.status == ConversationStatus.ARCHIVED:
                return conv.model_copy(deep=True)

            conv.status = ConversationStatus.ARCHIVED
            conv.updated_at = datetime.now(UTC)
            self._conversations[conversation_id] = conv
            return conv.model_copy(deep=True)

    async def restore_conversation(self, conversation_id: UUID) -> Conversation:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.status == ConversationStatus.DELETED:
                raise InvalidConversationStateError(
                    f"Cannot restore deleted conversation {conversation_id}.",
                    details={"conversation_id": str(conversation_id)},
                )
            if conv.status == ConversationStatus.ACTIVE:
                return conv.model_copy(deep=True)

            conv.status = ConversationStatus.ACTIVE
            conv.updated_at = datetime.now(UTC)
            self._conversations[conversation_id] = conv
            return conv.model_copy(deep=True)

    async def delete_conversation(self, conversation_id: UUID, soft_delete: bool = True) -> bool:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            conv = self._conversations.get(conversation_id)
            if conv is None:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found.",
                    details={"conversation_id": str(conversation_id)},
                )
            if soft_delete:
                conv.status = ConversationStatus.DELETED
                conv.deleted_at = datetime.now(UTC)
                conv.updated_at = datetime.now(UTC)
                self._conversations[conversation_id] = conv
            else:
                del self._conversations[conversation_id]
                self._messages.pop(conversation_id, None)
            return True

    async def create_message(self, message: Message) -> Message:
        lock = await self._get_conv_lock(message.conversation_id)
        async with lock:
            conv = self._conversations.get(message.conversation_id)
            if conv is None:
                raise ConversationNotFoundError(
                    f"Conversation {message.conversation_id} not found.",
                    details={"conversation_id": str(message.conversation_id)},
                )
            if conv.status == ConversationStatus.DELETED:
                raise ConversationDeletedError(
                    f"Cannot add message to deleted conversation {message.conversation_id}.",
                    details={"conversation_id": str(message.conversation_id)},
                )
            if conv.status == ConversationStatus.ARCHIVED:
                raise ConversationArchivedError(
                    f"Cannot add message to archived conversation {message.conversation_id}.",
                    details={"conversation_id": str(message.conversation_id)},
                )

            msg_list = self._messages.get(message.conversation_id, [])
            msg_copy = message.model_copy(deep=True)
            msg_list.append(msg_copy)
            self._messages[message.conversation_id] = msg_list

            # Update conversation metadata
            conv.message_count = len(msg_list)
            conv.last_message_at = msg_copy.created_at
            conv.updated_at = datetime.now(UTC)
            self._conversations[message.conversation_id] = conv

            return msg_copy.model_copy(deep=True)

    async def get_message(self, message_id: UUID) -> Message | None:
        async with self._global_lock:
            for msg_list in self._messages.values():
                for msg in msg_list:
                    if msg.message_id == message_id:
                        return msg.model_copy(deep=True)
            return None

    async def get_message_by_client_id(
        self, conversation_id: UUID, client_message_id: str
    ) -> Message | None:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            msg_list = self._messages.get(conversation_id, [])
            for msg in msg_list:
                if msg.client_message_id == client_message_id:
                    return msg.model_copy(deep=True)
            return None

    async def list_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
        asc: bool = True,
    ) -> tuple[list[Message], int]:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.status == ConversationStatus.DELETED:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found.",
                    details={"conversation_id": str(conversation_id)},
                )

            msg_list = list(self._messages.get(conversation_id, []))
            msg_list.sort(key=lambda m: m.sequence, reverse=not asc)
            total = len(msg_list)
            paginated = msg_list[offset : offset + limit]
            return [m.model_copy(deep=True) for m in paginated], total

    async def get_latest_messages(self, conversation_id: UUID, limit: int = 100) -> list[Message]:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.status == ConversationStatus.DELETED:
                raise ConversationNotFoundError(
                    f"Conversation {conversation_id} not found.",
                    details={"conversation_id": str(conversation_id)},
                )

            msg_list = list(self._messages.get(conversation_id, []))
            # Sort chronological
            msg_list.sort(key=lambda m: m.sequence)
            latest = msg_list[-limit:] if len(msg_list) > limit else msg_list
            return [m.model_copy(deep=True) for m in latest]

    async def get_next_sequence(self, conversation_id: UUID) -> int:
        lock = await self._get_conv_lock(conversation_id)
        async with lock:
            msg_list = self._messages.get(conversation_id, [])
            if not msg_list:
                return 1
            max_seq = max(m.sequence for m in msg_list)
            return max_seq + 1
