"""Domain exceptions for Module 22 — Coding Agent."""


class CodingAgentError(Exception):
    """Base exception for all Coding Agent errors."""

    def __init__(self, message: str, code: str = "CODING_AGENT_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class CodingSessionNotFoundError(CodingAgentError):
    """Raised when a requested coding session is not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Coding session '{session_id}' was not found.",
            code="SESSION_NOT_FOUND",
        )


class RepositoryNotFoundError(CodingAgentError):
    """Raised when a specified repository root directory does not exist or is invalid."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Repository root directory '{path}' does not exist or is invalid.",
            code="REPOSITORY_NOT_FOUND",
        )


class StalePatchError(CodingAgentError):
    """Raised when target file content has changed since patch creation."""

    def __init__(self, file_path: str) -> None:
        super().__init__(
            f"Stale patch detected for file '{file_path}'. File content changed since analysis.",
            code="STALE_PATCH",
        )


class ProtectedPathError(CodingAgentError):
    """Raised when an operation attempts to access or modify a restricted path (.env, keys, etc.)."""

    def __init__(self, path: str) -> None:
        super().__init__(
            f"Path '{path}' is protected by security policy.",
            code="PROTECTED_PATH_ERROR",
        )


class InvalidCodingPlanError(CodingAgentError):
    """Raised when a generated code plan is invalid or out of scope."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"Invalid coding plan: {reason}",
            code="INVALID_CODING_PLAN",
        )


class ValidationFailedError(CodingAgentError):
    """Raised when automated code validation (test/build/lint/typecheck) fails."""

    def __init__(self, stage: str, details: str) -> None:
        super().__init__(
            f"Validation failed during '{stage}': {details}",
            code="VALIDATION_FAILED",
        )


class MaxFixAttemptsExceededError(CodingAgentError):
    """Raised when bounded fix iteration loop reaches maximum allowed attempts."""

    def __init__(self, max_attempts: int) -> None:
        super().__init__(
            f"Debugging fix loop exceeded maximum limit of {max_attempts} attempts.",
            code="MAX_FIX_ATTEMPTS_EXCEEDED",
        )


class RollbackFailedError(CodingAgentError):
    """Raised when rolling back a changeset fails."""

    def __init__(self, changeset_id: str, reason: str) -> None:
        super().__init__(
            f"Failed to rollback changeset '{changeset_id}': {reason}",
            code="ROLLBACK_FAILED",
        )


class CodePromptInjectionDetectedError(CodingAgentError):
    """Raised when untrusted source code comments or README files attempt prompt injection."""

    def __init__(self, details: str) -> None:
        super().__init__(
            f"Prompt injection signal detected in code/repository content: {details}",
            code="CODE_PROMPT_INJECTION_DETECTED",
        )
