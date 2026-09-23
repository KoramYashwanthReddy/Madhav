"""Configuration exception definitions for MADHAV platform."""

from typing import Any

from madhav.core.exceptions import MadhavException


class ConfigurationError(MadhavException):
    """Exception raised when configuration loading or validation fails."""

    def __init__(
        self,
        message: str = "Invalid configuration provided.",
        code: str = "CONFIGURATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
