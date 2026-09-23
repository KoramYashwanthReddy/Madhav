"""Enumerations for AI Runtime domain concepts."""

from enum import StrEnum, auto


class AIRole(StrEnum):
    """Message sender role in AI conversation context."""

    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()


class FinishReason(StrEnum):
    """Normalized reason for completion of AI inference."""

    STOP = auto()
    LENGTH = auto()
    CANCELLED = auto()
    ERROR = auto()
    UNKNOWN = auto()


class StreamEventType(StrEnum):
    """Type indicator for AI streaming events."""

    STARTED = auto()
    DELTA = auto()
    COMPLETED = auto()
    ERROR = auto()


class RuntimeHealthStatus(StrEnum):
    """Health status reported by an AI runtime backend."""

    AVAILABLE = auto()
    UNAVAILABLE = auto()
    DEGRADED = auto()
    UNKNOWN = auto()
