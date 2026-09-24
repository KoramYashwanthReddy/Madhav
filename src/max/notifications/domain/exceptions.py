"""Domain exceptions for Module 27 — Notification System."""

from typing import Any


class NotificationError(Exception):
    """Base exception for all Notification System errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotificationValidationError(NotificationError):
    """Raised when notification parameters or content violate validation rules."""


class NotificationNotFoundError(NotificationError):
    """Raised when a requested notification or preference is not found."""


class NotificationChannelError(NotificationError):
    """Raised when a delivery channel is unavailable or misconfigured."""


class NotificationDeliveryError(NotificationError):
    """Raised when delivery to a channel provider fails."""


class NotificationPermissionError(NotificationError):
    """Raised when notification action or channel violates Module 15 security."""


class NotificationPolicyError(NotificationError):
    """Raised when notification violates system or sensitivity policies."""


class NotificationTemplateError(NotificationError):
    """Raised when template rendering or lookup fails."""


class NotificationRateLimitError(NotificationError):
    """Raised when rate limits suppress or delay notification delivery."""


class NotificationDeduplicatedError(NotificationError):
    """Raised when duplicate notification is suppressed by deduplication policy."""


class NotificationSecurityError(NotificationError):
    """Raised when notification violates security boundaries or secret protection."""
