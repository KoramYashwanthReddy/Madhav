"""Domain enumerations for Memory Engine."""

from enum import StrEnum


class MemoryType(StrEnum):
    """Extensible memory categories."""

    FACT = "fact"
    PREFERENCE = "preference"
    PERSONAL = "personal"
    GOAL = "goal"
    HABIT = "habit"
    DECISION = "decision"
    EXPERIENCE = "experience"
    RELATIONSHIP = "relationship"
    INSTRUCTION = "instruction"
    CONSTRAINT = "constraint"
    OTHER = "other"


class MemoryStatus(StrEnum):
    """Lifecycle state of a memory record."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    DELETED = "deleted"


class MemoryImportance(StrEnum):
    """Controlled importance rating scale."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MemoryConfidence(StrEnum):
    """Confidence rating of recorded memory."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MemorySource(StrEnum):
    """Origin source indicator for recorded memory."""

    USER_EXPLICIT = "user_explicit"
    USER_CONVERSATION = "user_conversation"
    SYSTEM = "system"
    IMPORTED = "imported"
    MANUAL = "manual"
    FUTURE_AI_INFERENCE = "future_ai_inference"


class MemoryScope(StrEnum):
    """Ownership and visibility scope of memory record."""

    USER = "user"
