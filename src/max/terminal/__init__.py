"""Module 18 — Terminal Agent package for Max Personal AI System.

Provides controlled, permission-aware, auditable command-line execution
across Windows PowerShell, CMD, and WSL backends.

Security flow:
    Agent
      ↓ tool call
    ToolRegistry  (Module 14)
      ↓ forwards
    PermissionGate  (Module 15)  ← first authorization check
      ↓ ALLOWED
    CommandPolicyService         ← structural second check (risk classification)
      ↓ ALLOWED
    TerminalBackend              ← actual subprocess (shell=False)
"""

from max.terminal.backends import (
    MockTerminalBackend,
    TerminalBackend,
    WindowsTerminalBackend,
    WSLTerminalBackend,
)
from max.terminal.container import (
    TerminalContainer,
    get_terminal_container,
    reset_terminal_container,
)
from max.terminal.domain import (
    CommandCategory,
    CommandClassification,
    CommandFailureReason,
    CommandPermissionDeniedError,
    CommandPolicyRejectionError,
    CommandRequest,
    CommandResult,
    CommandRiskLevel,
    CommandStatus,
    CommandTimeoutError,
    InvalidCommandError,
    PromptInjectionDefenseError,
    SessionNotFoundError,
    SessionStatus,
    ShellUnavailableError,
    TerminalError,
    TerminalSession,
    TerminalShell,
    TerminalSubsystemDisabledError,
    TerminalTraceEvent,
    WorkingDirectoryViolationError,
)
from max.terminal.security import CommandPolicyService
from max.terminal.services import TerminalService, register_terminal_tools

__all__ = [
    # Backends
    "TerminalBackend",
    "WindowsTerminalBackend",
    "WSLTerminalBackend",
    "MockTerminalBackend",
    # Container
    "TerminalContainer",
    "get_terminal_container",
    "reset_terminal_container",
    # Domain Enums
    "TerminalShell",
    "CommandRiskLevel",
    "CommandStatus",
    "CommandFailureReason",
    "SessionStatus",
    "CommandCategory",
    # Domain Exceptions
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
    # Domain Models
    "CommandRequest",
    "CommandResult",
    "CommandClassification",
    "TerminalSession",
    "TerminalTraceEvent",
    # Security
    "CommandPolicyService",
    # Services
    "TerminalService",
    "register_terminal_tools",
]
