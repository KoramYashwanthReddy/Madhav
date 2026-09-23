"""Memory Engine subsystem custom exceptions."""

from typing import Any

from max.core.exceptions import MaxException


class MemoryEngineError(MaxException):
    """Base exception for all Memory Engine failures."""

    def __init__(
        self,
        message: str = "A memory engine processing error occurred.",
        code: str = "MEMORY_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MemoryNotFoundError(MemoryEngineError):
    """Raised when a requested memory record is not found."""

    def __init__(
        self,
        message: str = "Memory record not found.",
        code: str = "MEMORY_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MemoryValidationError(MemoryEngineError):
    """Raised when memory content or payload fails validation."""

    def __init__(
        self,
        message: str = "Memory validation failed.",
        code: str = "MEMORY_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class DuplicateMemoryError(MemoryEngineError):
    """Raised when a duplicate memory is detected upon creation."""

    def __init__(
        self,
        message: str = "A duplicate memory record already exists.",
        code: str = "DUPLICATE_MEMORY",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidMemoryStateTransitionError(MemoryEngineError):
    """Raised when an invalid lifecycle state transition is requested."""

    def __init__(
        self,
        message: str = "Invalid memory lifecycle state transition.",
        code: str = "INVALID_MEMORY_STATE_TRANSITION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MemoryOwnershipError(MemoryEngineError):
    """Raised when an identity attempts to access or mutate a memory owned by another identity."""

    def __init__(
        self,
        message: str = "Access to memory denied due to owner mismatch.",
        code: str = "MEMORY_OWNERSHIP_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MemoryExpiredError(MemoryEngineError):
    """Raised when an operation is performed on an expired memory record."""

    def __init__(
        self,
        message: str = "Memory record has expired.",
        code: str = "MEMORY_EXPIRED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class MemoryDeletedError(MemoryEngineError):
    """Raised when an operation is performed on a deleted memory record."""

    def __init__(
        self,
        message: str = "Memory record has been deleted.",
        code: str = "MEMORY_DELETED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
