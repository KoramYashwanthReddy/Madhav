"""Context Management domain enumerations."""

from enum import IntEnum, StrEnum


class ContextCategory(StrEnum):
    """Categorization taxonomy for candidate context items."""

    SYSTEM = "system"
    IDENTITY = "identity"
    REQUEST = "request"
    CONVERSATION = "conversation"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    INSTRUCTION = "instruction"
    TOOL_RESULT = "tool_result"
    OTHER = "other"


class ContextPriority(IntEnum):
    """Deterministic priority levels for context selection (higher integer = higher priority)."""

    CRITICAL = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    OPTIONAL = 1

    @classmethod
    def from_string(cls, val: str) -> "ContextPriority":
        """Parse priority level string into ContextPriority enum."""
        mapping = {
            "CRITICAL": cls.CRITICAL,
            "HIGH": cls.HIGH,
            "NORMAL": cls.NORMAL,
            "LOW": cls.LOW,
            "OPTIONAL": cls.OPTIONAL,
        }
        upper_val = val.strip().upper()
        if upper_val not in mapping:
            valid_keys = list(mapping.keys())
            raise ValueError(f"Unknown ContextPriority level '{val}'. Valid options: {valid_keys}")
        return mapping[upper_val]


class TruncationStrategy(StrEnum):
    """Strategy for truncating oversized context item content."""

    NONE = "none"
    TAIL = "tail"
    HEAD = "head"
    HEAD_AND_TAIL = "head_and_tail"


class SourceTrustLevel(StrEnum):
    """Trust classification level assigned to context item origins."""

    SYSTEM = "system"
    TRUSTED = "trusted"
    NORMAL = "normal"
    UNTRUSTED = "untrusted"
