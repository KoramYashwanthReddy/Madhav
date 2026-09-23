"""Centralized exception hierarchy for MAX platform foundation."""

from typing import Any


class MaxException(Exception):
    """Base exception class for all MAX platform errors."""

    def __init__(
        self,
        message: str = "An internal MAX platform error occurred.",
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
        self.status_code = status_code


class ApplicationError(MaxException):
    """General application domain logic error."""

    def __init__(
        self,
        message: str = "Application processing error.",
        code: str = "APPLICATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ValidationError(MaxException):
    """Input parameters or schema validation failure."""

    def __init__(
        self,
        message: str = "Request validation failed.",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class NotFoundError(MaxException):
    """Requested resource was not found."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InternalError(MaxException):
    """Unexpected internal server error."""

    def __init__(
        self,
        message: str = "An internal error occurred.",
        code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
