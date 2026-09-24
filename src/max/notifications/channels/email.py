"""Email notification provider implementation."""

from __future__ import annotations

import logging
import time
from typing import Any

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt

logger = logging.getLogger(__name__)


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider handling SMTP configuration boundaries."""

    def __init__(self, smtp_enabled: bool = False, sender_address: str = "max@localhost") -> None:
        self.smtp_enabled = smtp_enabled
        self.sender_address = sender_address

    @property
    def provider_name(self) -> str:
        return "email_smtp"

    def supports_channel(self, channel: NotificationChannelType) -> bool:
        return channel == NotificationChannelType.EMAIL

    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        start_time = time.monotonic()

        if not self.smtp_enabled:
            elapsed_ms = (time.monotonic() - start_time) * 1000.0
            logger.info("Email delivery skipped — SMTP is disabled by configuration.")
            return NotificationDeliveryAttempt(
                attempt_number=1,
                status=NotificationDeliveryStatus.FAILED,
                error_code="SMTP_DISABLED",
                error_message="SMTP email delivery is disabled in system configuration.",
                duration_ms=elapsed_ms,
            )

        recipient_email = notification.recipient.email or "user@localhost"
        logger.info("Sending mock email to %s for notification %s", recipient_email, notification.notification_id)
        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return NotificationDeliveryAttempt(
            attempt_number=1,
            status=NotificationDeliveryStatus.SUCCESS,
            provider_reference=f"smtp_msg_{notification.notification_id}",
            duration_ms=elapsed_ms,
        )

    async def cancel(self, notification_id: str) -> bool:
        return False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "email_smtp",
            "smtp_enabled": self.smtp_enabled,
            "supports_html": True,
            "supports_templates": True,
        }
