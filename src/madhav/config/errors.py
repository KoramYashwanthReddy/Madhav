"""Configuration exception classes for MADHAV."""

from typing import Any

from madhav.core.exceptions import MadhavException


class ConfigurationError(MadhavException):
    """Base exception for configuration loading or initialization errors."""

    def __init__(
        self,
        message: str = "Configuration processing error.",
        code: str = "CONFIGURATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ConfigurationValidationError(ConfigurationError):
    """Raised when configuration validation checks fail."""

    def __init__(
        self,
        message: str = "Configuration validation check failed.",
        code: str = "CONFIGURATION_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=500)
