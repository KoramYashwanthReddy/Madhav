"""Unit tests for ConversationService facade and Turn Service."""

import pytest

from madhav.conversation.domain.enums import MessageRole
from madhav.conversation.exceptions import (
    ConversationArchivedError,
    ConversationDeletedError,
    MessageValidationError,
)
from madhav.conversation.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_conversation_service_creation_and_title() -> None:
    """Verify conversation service creation, title updates, and summary listing."""
    service = ConversationService()

    conv = await service.create_conversation(owner_id="user_test", title="Design Plan")
    assert conv.owner_id == "user_test"
    assert conv.title == "Design Plan"

    # Explicit title update
    updated = await service.update_title(conv.conversation_id, "Updated Design Plan")
    assert updated.title == "Updated Design Plan"

    # Listing
    summaries, total = await service.list_conversations(owner_id="user_test")
    assert total == 1
    assert summaries[0].title == "Updated Design Plan"


@pytest.mark.asyncio
async def test_conversation_service_turn_execution() -> None:
    """Verify executing a conversation turn through ConversationService."""
    service = ConversationService()
    conv = await service.create_conversation(owner_id="user_test")

    # Send first message (should trigger auto-title generation)
    result = await service.send_message(
        conversation_id=conv.conversation_id,
        content="How do I build a scalable microservices architecture?",
    )

    assert result.user_message.role == MessageRole.USER
    assert result.user_message.content == "How do I build a scalable microservices architecture?"
    assert result.assistant_message.role == MessageRole.ASSISTANT
    assert len(result.assistant_message.content) > 0

    # Auto title should be generated
    assert result.conversation.title == "How do I build a scalable microservices architecture?"
    assert result.conversation.message_count == 2


@pytest.mark.asyncio
async def test_conversation_service_idempotency() -> None:
    """Verify client_message_id idempotency prevents duplicate user messages."""
    service = ConversationService()
    conv = await service.create_conversation(owner_id="user_test")

    client_id = "client-unique-key-123"

    res1 = await service.send_message(
        conversation_id=conv.conversation_id,
        content="Test prompt",
        client_message_id=client_id,
    )

    # Resend identical request with same client_message_id
    res2 = await service.send_message(
        conversation_id=conv.conversation_id,
        content="Test prompt",
        client_message_id=client_id,
    )

    assert res1.user_message.message_id == res2.user_message.message_id
    assert res1.assistant_message.message_id == res2.assistant_message.message_id

    # Total messages in conversation must still be 2 (1 turn)
    history = await service.list_messages(conv.conversation_id)
    assert history.total_messages == 2


@pytest.mark.asyncio
async def test_conversation_service_validation_errors() -> None:
    """Verify validation and state error conditions."""
    service = ConversationService()
    conv = await service.create_conversation(owner_id="user_test")

    # Empty content error
    with pytest.raises(MessageValidationError):
        await service.send_message(conv.conversation_id, content="   ")

    # Archived conversation error
    await service.archive_conversation(conv.conversation_id)
    with pytest.raises(ConversationArchivedError):
        await service.send_message(conv.conversation_id, content="Hello")

    # Deleted conversation error
    await service.restore_conversation(conv.conversation_id)
    await service.delete_conversation(conv.conversation_id, soft_delete=True)
    with pytest.raises(ConversationDeletedError):
        await service.send_message(conv.conversation_id, content="Hello")
