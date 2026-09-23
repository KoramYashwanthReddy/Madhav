"""Enumeration types for the Identity & Personal Profile subsystem."""

from enum import StrEnum, auto


class ResponseStyle(StrEnum):
    """Preferred assistant response style."""

    CONCISE = auto()
    BALANCED = auto()
    DETAILED = auto()


class Verbosity(StrEnum):
    """Verbosity level preference for assistant explanations."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()


class ConfirmationPreference(StrEnum):
    """User preference for action confirmation before execution."""

    ALWAYS = auto()
    SENSITIVE_ACTIONS = auto()
    NEVER = auto()


class CommunicationChannel(StrEnum):
    """Preferred communication channel identifier."""

    TEXT = auto()
    VOICE = auto()
    SYSTEM_NOTIFICATION = auto()
