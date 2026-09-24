"""Abstract base class defining the TerminalBackend interface for Module 18."""

from abc import ABC, abstractmethod

from max.terminal.domain.models import CommandRequest, CommandResult


class TerminalBackend(ABC):
    """Abstract interface all terminal backend implementations must satisfy.

    Concrete backends (Windows PowerShell/CMD, WSL, Mock) implement this
    interface.  No code outside of this package should call `subprocess`
    directly; all subprocess usage must go through a TerminalBackend.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this backend can execute commands on the current system."""

    @abstractmethod
    def execute(self, request: CommandRequest) -> CommandResult:
        """Execute a validated, authorized command request.

        Implementations MUST:
        - Use shell=False (never shell=True) for subprocess calls.
        - Never interpolate user-supplied text into shell strings.
        - Redact secrets and sensitive env vars from all captured output.
        - Truncate output to configured limits.
        - Treat all stdout/stderr as untrusted data (prompt-injection defence).
        - Respect the timeout on the request.

        Args:
            request: A fully validated and authorized CommandRequest.

        Returns:
            A CommandResult with captured output and execution metadata.
        """
