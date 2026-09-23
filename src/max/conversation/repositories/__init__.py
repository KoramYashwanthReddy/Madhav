"""Conversation repositories export module."""

from max.conversation.repositories.base import ConversationRepository
from max.conversation.repositories.memory import InMemoryConversationRepository

__all__ = [
    "ConversationRepository",
    "InMemoryConversationRepository",
]
