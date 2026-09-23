"""End-to-End integration test for Module 07 Multi-Turn Conversation flow."""

import pytest

from max.conversation.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_end_to_end_multi_turn_conversation_flow() -> None:
    """Verify multi-turn conversation flow completely offline.

    Ensures that prior conversation turns are supplied via ConversationContextSource
    to Module 06 ContextManager and assembled for Module 04 AI Runtime inference.
    """
    service = ConversationService()

    # 1. Create a new conversation
    conv = await service.create_conversation(owner_id="e2e_owner", title="Multi-Turn E2E Test")
    assert conv.status.value == "active"

    # 2. Turn 1: Send initial user message
    turn1 = await service.send_message(
        conversation_id=conv.conversation_id,
        content="Hello Max, I am working on building a modular AI system.",
        owner_id="e2e_owner",
    )

    assert (
        turn1.user_message.content == "Hello Max, I am working on building a modular AI system."
    )
    assert turn1.assistant_message.status.value == "completed"
    assert len(turn1.assistant_message.content) > 0

    # 3. Turn 2: Send follow-up question referencing turn 1 context
    turn2 = await service.send_message(
        conversation_id=conv.conversation_id,
        content="What was the topic of my previous message?",
        owner_id="e2e_owner",
    )

    assert turn2.user_message.sequence == 3
    assert turn2.assistant_message.sequence == 4
    assert turn2.conversation.message_count == 4

    # Verify history contains all 4 messages in chronological sequence
    history = await service.list_messages(conv.conversation_id)
    assert history.total_messages == 4
    assert [m.sequence for m in history.messages] == [1, 2, 3, 4]
    assert [m.role.value for m in history.messages] == ["user", "assistant", "user", "assistant"]
