"""AI Runtime subsystem custom exceptions."""

from typing import Any

from max.core.exceptions import MaxException


class AIRuntimeError(MaxException):
    """Base exception for all AI Runtime failures."""

    def __init__(
        self,
        message: str = "An AI runtime processing error occurred.",
        code: str = "AI_RUNTIME_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class AIValidationError(AIRuntimeError):
    """Raised when an AI request payload or configuration fails validation."""

    def __init__(
        self,
        message: str = "AI request validation failed.",
        code: str = "AI_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class AIRuntimeUnavailableError(AIRuntimeError):
    """Raised when requested AI runtime backend is unavailable or offline."""

    def __init__(
        self,
        message: str = "The requested AI runtime backend is currently unavailable.",
        code: str = "AI_RUNTIME_UNAVAILABLE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 503,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class AIInferenceTimeoutError(AIRuntimeError):
    """Raised when AI inference exceeds allocated execution timeout."""

    def __init__(
        self,
        message: str = "AI inference execution timed out.",
        code: str = "AI_INFERENCE_TIMEOUT",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 504,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class AIInferenceCancelledError(AIRuntimeError):
    """Raised when in-flight AI inference execution is cancelled."""

    def __init__(
        self,
        message: str = "AI inference execution was cancelled.",
        code: str = "AI_INFERENCE_CANCELLED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 499,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class AIResponseValidationError(AIRuntimeError):
    """Raised when AI provider response format is malformed or invalid."""

    def __init__(
        self,
        message: str = "AI provider response validation failed.",
        code: str = "AI_RESPONSE_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
