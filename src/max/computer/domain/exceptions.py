"""Domain exceptions for Module 16 — Computer Control."""

from typing import Any

from max.core.exceptions import MaxException


class ComputerControlError(MaxException):
    """Base exception for all computer control errors."""

    def __init__(
        self,
        message: str = "A computer control error occurred.",
        code: str = "COMPUTER_CONTROL_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class BackendUnavailableError(ComputerControlError):
    """Computer control OS backend is unavailable or unsupported."""

    def __init__(
        self,
        message: str = "Computer control backend is unavailable.",
        code: str = "BACKEND_UNAVAILABLE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 503,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class DisplayNotFoundError(ComputerControlError):
    """Target display was not found."""

    def __init__(
        self,
        message: str = "Target display not found.",
        code: str = "DISPLAY_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class WindowNotFoundError(ComputerControlError):
    """Target window was not found."""

    def __init__(
        self,
        message: str = "Target window not found.",
        code: str = "WINDOW_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidComputerActionError(ComputerControlError):
    """Action request or parameters are invalid."""

    def __init__(
        self,
        message: str = "Invalid computer action request parameters.",
        code: str = "INVALID_COMPUTER_ACTION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class OutOfBoundsError(ComputerControlError):
    """Mouse coordinate or window dimension is out of bounds."""

    def __init__(
        self,
        message: str = "Coordinates or window size are out of bounds.",
        code: str = "OUT_OF_BOUNDS",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ComputerPermissionError(ComputerControlError):
    """Computer control action lacks valid authorization token from Module 15."""

    def __init__(
        self,
        message: str = "Action lacks valid Module 15 security authorization.",
        code: str = "COMPUTER_PERMISSION_DENIED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ComputerActionTimeoutError(ComputerControlError):
    """Computer control action execution timed out."""

    def __init__(
        self,
        message: str = "Computer control action timed out.",
        code: str = "ACTION_TIMEOUT",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 408,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ComputerActionCancelledError(ComputerControlError):
    """Computer control action was cancelled."""

    def __init__(
        self,
        message: str = "Computer control action was cancelled.",
        code: str = "ACTION_CANCELLED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ComputerVerificationError(ComputerControlError):
    """Computer control action post-execution state verification failed."""

    def __init__(
        self,
        message: str = "Computer action post-execution verification failed.",
        code: str = "VERIFICATION_FAILED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ComputerSecurityBlockedError(ComputerControlError):
    """Action was blocked by security mode or active emergency block."""

    def __init__(
        self,
        message: str = "Computer control action was blocked by security policy.",
        code: str = "COMPUTER_SECURITY_BLOCKED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)

