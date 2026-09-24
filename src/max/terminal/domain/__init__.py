"""Domain package for Module 18 — Terminal Agent."""

from max.terminal.domain.enums import (
    CommandCategory,
    CommandFailureReason,
    CommandRiskLevel,
    CommandStatus,
    SessionStatus,
    TerminalShell,
)
from max.terminal.domain.exceptions import (
    CommandPermissionDeniedError,
    CommandPolicyRejectionError,
    CommandTimeoutError,
    InvalidCommandError,
    PromptInjectionDefenseError,
    SessionNotFoundError,
    ShellUnavailableError,
    TerminalError,
    TerminalSubsystemDisabledError,
    WorkingDirectoryViolationError,
)
from max.terminal.domain.models import (
    CommandClassification,
    CommandRequest,
    CommandResult,
    TerminalSession,
    TerminalTraceEvent,
)

__all__ = [
    # Enums
    "TerminalShell",
    "CommandRiskLevel",
    "CommandStatus",
    "CommandFailureReason",
    "SessionStatus",
    "CommandCategory",
    # Exceptions
    "TerminalError",
    "TerminalSubsystemDisabledError",
    "CommandPolicyRejectionError",
    "CommandPermissionDeniedError",
    "InvalidCommandError",
    "WorkingDirectoryViolationError",
    "ShellUnavailableError",
    "CommandTimeoutError",
    "SessionNotFoundError",
    "PromptInjectionDefenseError",
    # Models
    "CommandRequest",
    "CommandResult",
    "CommandClassification",
    "TerminalSession",
    "TerminalTraceEvent",
]
