from typing import Any


class PersonalizationError(Exception):
    """Base exception for Personalization subsystem errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PreferenceNotFoundError(PersonalizationError):
    """Raised when a requested preference cannot be found."""


class HypothesisNotFoundError(PersonalizationError):
    """Raised when a requested hypothesis cannot be found."""


class InvalidPreferenceError(PersonalizationError):
    """Raised when preference structure or value is invalid."""


class SensitiveInferenceViolationError(PersonalizationError):
    """Raised when an attempt is made to infer or store forbidden sensitive traits."""


class PermissionEscalationViolationError(PersonalizationError):
    """Raised when learning or AI hypotheses attempt to alter security authority or permissions."""


class PreferenceConflictError(PersonalizationError):
    """Raised when irreconcilable preference conflicts occur."""
