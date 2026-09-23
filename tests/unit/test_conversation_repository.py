"""Unit tests for InMemoryConversationRepository operations and concurrency."""

import asyncio

import pytest

from madhav.conversation.domain.conversation import Conversation
from madhav.conversation.domain.enums import ConversationStatus, MessageRole
from madhav.conversation.domain.message import Message
from madhav.conversation.exceptions import (
    ConversationArchivedError,
    ConversationDeletedError,
)
from madhav.conversation.repositories.memory import InMemoryConversationRepository


@pytest.mark.asyncio
async def test_repository_conversation_crud() -> None:
    """Verify conversation CRUD operations in InMemoryConversationRepository."""
    repo = InMemoryConversationRepository()

    # Create
    conv = Conversation(owner_id="owner_1", title="Test Conversation")
    saved = await repo.create_conversation(conv)
    assert saved.conversation_id == conv.conversation_id

    # Retrieve
    retrieved = await repo.get_conversation(saved.conversation_id)
    assert retrieved is not None
    assert retrieved.title == "Test Conversation"

    # List
    convs, total = await repo.list_conversations(owner_id="owner_1")
    assert total == 1
    assert convs[0].conversation_id == saved.conversation_id

    # Update
    saved.title = "Updated Title"
    updated = await repo.update_conversation(saved)
    assert updated.title == "Updated Title"

    # Archive
    archived = await repo.archive_conversation(saved.conversation_id)
    assert archived.status == ConversationStatus.ARCHIVED

    # Restore
    restored = await repo.restore_conversation(saved.conversation_id)
    assert restored.status == ConversationStatus.ACTIVE

    # Delete
    deleted = await repo.delete_conversation(saved.conversation_id, soft_delete=True)
    assert deleted is True

    # List should now exclude soft deleted conversation
    convs_after, total_after = await repo.list_conversations(owner_id="owner_1")
    assert total_after == 0


@pytest.mark.asyncio
async def test_repository_message_creation_and_sequence() -> None:
    """Verify message persistence, sequence generation, and metadata updating."""
    repo = InMemoryConversationRepository()
    conv = await repo.create_conversation(Conversation(owner_id="owner_1"))

    seq1 = await repo.get_next_sequence(conv.conversation_id)
    assert seq1 == 1

    msg1 = Message(
        conversation_id=conv.conversation_id,
        sequence=seq1,
        role=MessageRole.USER,
        content="First message",
    )
    saved_msg1 = await repo.create_message(msg1)
    assert saved_msg1.sequence == 1

    # Verify conversation metadata updated
    updated_conv = await repo.get_conversation(conv.conversation_id)
    assert updated_conv is not None
    assert updated_conv.message_count == 1
    assert updated_conv.last_message_at is not None

    seq2 = await repo.get_next_sequence(conv.conversation_id)
    assert seq2 == 2

    msg2 = Message(
        conversation_id=conv.conversation_id,
        sequence=seq2,
        role=MessageRole.ASSISTANT,
        content="First response",
    )
    await repo.create_message(msg2)

    msgs, total_msgs = await repo.list_messages(conv.conversation_id)
    assert total_msgs == 2
    assert msgs[0].sequence == 1
    assert msgs[1].sequence == 2


@pytest.mark.asyncio
async def test_repository_archived_and_deleted_restrictions() -> None:
    """Verify that archived or deleted conversations reject message additions."""
    repo = InMemoryConversationRepository()
    conv = await repo.create_conversation(Conversation(owner_id="owner_1"))

    # Archive
    await repo.archive_conversation(conv.conversation_id)

    msg = Message(
        conversation_id=conv.conversation_id,
        sequence=1,
        role=MessageRole.USER,
        content="Test in archive",
    )
    with pytest.raises(ConversationArchivedError):
        await repo.create_message(msg)

    # Restore & Soft Delete
    await repo.restore_conversation(conv.conversation_id)
    await repo.delete_conversation(conv.conversation_id, soft_delete=True)

    with pytest.raises(ConversationDeletedError):
        await repo.create_message(msg)


@pytest.mark.asyncio
async def test_concurrent_message_sequence_generation() -> None:
    """Verify sequence generation remains unique under concurrent operations."""
    repo = InMemoryConversationRepository()
    conv = await repo.create_conversation(Conversation(owner_id="owner_1"))

    async def add_concurrent_message(idx: int) -> int:
        seq = await repo.get_next_sequence(conv.conversation_id)
        msg = Message(
            conversation_id=conv.conversation_id,
            sequence=seq,
            role=MessageRole.USER,
            content=f"Concurrent message {idx}",
        )
        saved = await repo.create_message(msg)
        return saved.sequence

    tasks = [add_concurrent_message(i) for i in range(20)]
    sequences = await asyncio.gather(*tasks)

    # Sequences must be unique integers 1..20
    assert len(sequences) == 20
    assert len(set(sequences)) == 20
