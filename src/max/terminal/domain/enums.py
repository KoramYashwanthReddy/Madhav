"""Domain enumerations for Module 18 — Terminal Agent."""

from enum import StrEnum


class TerminalShell(StrEnum):
    """Available terminal shell backends."""

    POWERSHELL = "POWERSHELL"
    CMD = "CMD"
    WSL = "WSL"
    MOCK = "MOCK"


class CommandRiskLevel(StrEnum):
    """Risk classification for terminal commands."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CommandStatus(StrEnum):
    """Lifecycle state for a command execution request."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    TIMED_OUT = "TIMED_OUT"
    SIMULATED = "SIMULATED"


class CommandFailureReason(StrEnum):
    """Structured failure reason taxonomy for terminal operations."""

    PERMISSION_DENIED = "PERMISSION_DENIED"
    POLICY_REJECTED = "POLICY_REJECTED"
    TIMEOUT = "TIMEOUT"
    PROCESS_ERROR = "PROCESS_ERROR"
    INVALID_COMMAND = "INVALID_COMMAND"
    WORKING_DIR_VIOLATION = "WORKING_DIR_VIOLATION"
    SHELL_UNAVAILABLE = "SHELL_UNAVAILABLE"
    SUBSYSTEM_DISABLED = "SUBSYSTEM_DISABLED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class SessionStatus(StrEnum):
    """State of a terminal session."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class CommandCategory(StrEnum):
    """Semantic category classification for commands."""

    FILESYSTEM = "FILESYSTEM"
    PROCESS = "PROCESS"
    NETWORK = "NETWORK"
    PACKAGE_MANAGER = "PACKAGE_MANAGER"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    CONTAINER = "CONTAINER"
    GIT = "GIT"
    TEXT_PROCESSING = "TEXT_PROCESSING"
    UNKNOWN = "UNKNOWN"
