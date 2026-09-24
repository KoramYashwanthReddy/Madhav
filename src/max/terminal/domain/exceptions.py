"""Domain exceptions for Module 18 — Terminal Agent."""


class TerminalError(Exception):
    """Base exception for all Terminal Agent errors."""


class TerminalSubsystemDisabledError(TerminalError):
    """Raised when the Terminal Agent subsystem is administratively disabled."""


class CommandPolicyRejectionError(TerminalError):
    """Raised when CommandPolicyService classifies a command as disallowed.

    This is the second line of defense after Module 15 PermissionGate.
    """


class CommandPermissionDeniedError(TerminalError):
    """Raised when Module 15 PermissionGate denies the terminal execute request."""


class InvalidCommandError(TerminalError):
    """Raised when the command or its arguments fail structural validation."""


class WorkingDirectoryViolationError(TerminalError):
    """Raised when the requested working directory is outside allowed roots."""


class ShellUnavailableError(TerminalError):
    """Raised when the requested shell backend is not available on this system."""


class CommandTimeoutError(TerminalError):
    """Raised when command execution exceeds the configured timeout limit."""


class SessionNotFoundError(TerminalError):
    """Raised when a referenced terminal session does not exist."""


class PromptInjectionDefenseError(TerminalError):
    """Raised when an execution request is detected to originate from untrusted output.

    Principle: Terminal output must never be interpreted as an authorization signal.
    """
