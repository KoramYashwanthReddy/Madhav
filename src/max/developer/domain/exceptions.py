"""Domain exceptions for Module 23 — Developer Agent."""


class DeveloperAgentError(Exception):
    """Base exception for all Developer Agent errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DevSessionNotFoundError(DeveloperAgentError):
    """Raised when a DeveloperSession cannot be found by its ID."""


class DevWorkflowNotFoundError(DeveloperAgentError):
    """Raised when a DeveloperWorkflow cannot be found by its ID."""


class DevIssueNotFoundError(DeveloperAgentError):
    """Raised when a DeveloperIssue cannot be found by its ID."""


class DevPRNotFoundError(DeveloperAgentError):
    """Raised when a PullRequest cannot be found by its ID."""


class GitOperationError(DeveloperAgentError):
    """Raised when a Git command fails (non-zero exit code)."""

    def __init__(self, message: str, command: str = "", exit_code: int = -1, stderr: str = "") -> None:
        super().__init__(message, details={"command": command, "exit_code": exit_code, "stderr": stderr})
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class RepositoryNotFoundError(DeveloperAgentError):
    """Raised when a path is not a valid Git repository."""


class BranchNotFoundError(DeveloperAgentError):
    """Raised when a requested branch does not exist."""


class PRConflictError(DeveloperAgentError):
    """Raised when a merge conflict prevents PR completion."""


class DevPermissionDeniedError(DeveloperAgentError):
    """Raised when a developer operation is blocked by policy or PermissionGate."""


PermissionDeniedError = DevPermissionDeniedError


class WorkflowTransitionError(DeveloperAgentError):
    """Raised when an invalid state machine transition is attempted."""


class WorkflowExecutionError(DeveloperAgentError):
    """Raised when a workflow step fails during execution."""
