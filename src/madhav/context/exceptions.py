"""Context Management subsystem custom exceptions."""

from typing import Any

from madhav.core.exceptions import MadhavException


class ContextError(MadhavException):
    """Base exception for all Context Management failures."""

    def __init__(
        self,
        message: str = "A context management processing error occurred.",
        code: str = "CONTEXT_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidContextError(ContextError):
    """Raised when context items, requests, or payload structures fail validation."""

    def __init__(
        self,
        message: str = "Context validation failed.",
        code: str = "CONTEXT_INVALID",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ContextBudgetExceededError(ContextError):
    """Raised when allocated token budget is exceeded and items cannot fit."""

    def __init__(
        self,
        message: str = "Context token budget exceeded.",
        code: str = "CONTEXT_BUDGET_EXCEEDED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class RequiredContextOverflowError(ContextError):
    """Raised when mandatory required context items exceed available token budget."""

    def __init__(
        self,
        message: str = "Required context items exceed available token budget.",
        code: str = "REQUIRED_CONTEXT_OVERFLOW",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ContextSourceError(ContextError):
    """Raised when a context source fails to supply or process context items."""

    def __init__(
        self,
        message: str = "Context source processing failed.",
        code: str = "CONTEXT_SOURCE_FAILED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ContextPolicyError(ContextError):
    """Raised when context policy is invalid or violates operational boundaries."""

    def __init__(
        self,
        message: str = "Context policy configuration error.",
        code: str = "CONTEXT_POLICY_INVALID",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
