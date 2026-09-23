"""Domain enumerations for Conversation Engine."""

from enum import StrEnum


class ConversationStatus(StrEnum):
    """Lifecycle states for a conversation."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MessageRole(StrEnum):
    """Participant roles in a conversation message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MessageStatus(StrEnum):
    """Lifecycle states for an individual message."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
