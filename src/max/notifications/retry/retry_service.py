"""Retry service for Module 27 — Notification System."""

from __future__ import annotations

import logging

from max.notifications.domain.enums import NotificationDeliveryStatus
from max.notifications.domain.models import NotificationDelivery, NotificationDeliveryAttempt

logger = logging.getLogger(__name__)

# Non-retryable error codes
PERMANENT_ERRORS = {
    "SMTP_DISABLED",
    "DESKTOP_DISABLED",
    "PUSH_DISABLED",
    "SPEECH_DISABLED",
    "PERMISSION_DENIED",
    "INVALID_RECIPIENT",
    "FORMAT_ERROR",
}


class NotificationRetryService:
    """Manages retry policies, backoff calculation, and permanent error detection."""

    def __init__(self, max_retries: int = 3, initial_delay_seconds: float = 2.0) -> None:
        self.max_retries = max_retries
        self.initial_delay_seconds = initial_delay_seconds

    def should_retry(self, delivery: NotificationDelivery, last_attempt: NotificationDeliveryAttempt) -> bool:
        """Determine if a failed delivery attempt should be retried."""
        if delivery.attempt_count >= self.max_retries:
            return False

        if last_attempt.error_code in PERMANENT_ERRORS:
            logger.info("Delivery attempt error '%s' is permanent — skipping retry.", last_attempt.error_code)
            return False

        return True

    def calculate_backoff_delay(self, attempt_count: int) -> float:
        """Calculate exponential backoff delay."""
        return self.initial_delay_seconds * (2 ** max(0, attempt_count - 1))
