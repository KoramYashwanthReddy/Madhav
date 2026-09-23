"""Unit tests for Module 07 Conversation domain models and Title Generator."""

from uuid import uuid4

from madhav.conversation.domain.conversation import Conversation
from madhav.conversation.domain.enums import ConversationStatus, MessageRole, MessageStatus
from madhav.conversation.domain.message import Message
from madhav.conversation.services.title_generator import DeterministicTitleGenerator


def test_conversation_domain_defaults() -> None:
    """Verify Conversation aggregate default values and helper methods."""
    conv = Conversation(owner_id="owner_123")
    assert conv.owner_id == "owner_123"
    assert conv.status == ConversationStatus.ACTIVE
    assert conv.is_active() is True
    assert conv.is_archived() is False
    assert conv.is_deleted() is False
    assert conv.title is None
    assert conv.message_count == 0


def test_message_domain_creation() -> None:
    """Verify Message entity domain properties."""
    conv_id = uuid4()
    msg = Message(
        conversation_id=conv_id,
        sequence=1,
        role=MessageRole.USER,
        content="Hello Madhav",
        status=MessageStatus.COMPLETED,
    )
    assert msg.conversation_id == conv_id
    assert msg.sequence == 1
    assert msg.role == MessageRole.USER
    assert msg.content == "Hello Madhav"
    assert msg.status == MessageStatus.COMPLETED


def test_deterministic_title_generator() -> None:
    """Verify DeterministicTitleGenerator creates clean titles without LLM."""
    generator = DeterministicTitleGenerator(max_length=30)

    # Simple prompt
    t1 = generator.generate_title("Help me design a Python app")
    assert t1 == "Help me design a Python app"

    # Multiline prompt with excess whitespace
    t2 = generator.generate_title("   \n   First line title  \n Second line content  ")
    assert t2 == "First line title"

    # Truncation
    t3 = generator.generate_title(
        "This is a very long user prompt that exceeds maximum allowed title length"
    )
    assert len(t3) <= 30
    assert t3.endswith("...")

    # Empty prompt fallback
    t4 = generator.generate_title("   ")
    assert t4 == "New conversation"
