"""Identity subsystem custom exceptions."""

from typing import Any

from max.core.exceptions import MaxException


class IdentityNotFoundError(MaxException):
    """Raised when an identity record or profile is not found."""

    def __init__(
        self,
        message: str = "Requested identity entity was not found.",
        code: str = "IDENTITY_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidProfileError(MaxException):
    """Raised when profile validation or field constraints fail."""

    def __init__(
        self,
        message: str = "Personal profile data is invalid.",
        code: str = "INVALID_PROFILE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidPreferenceError(MaxException):
    """Raised when preference validation fails."""

    def __init__(
        self,
        message: str = "Preference value or configuration is invalid.",
        code: str = "INVALID_PREFERENCE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
