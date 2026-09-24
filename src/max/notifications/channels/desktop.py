"""Desktop notification provider mock implementation."""

from __future__ import annotations

import logging
import time
from typing import Any

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt

logger = logging.getLogger(__name__)


class MockDesktopNotificationProvider(NotificationProvider):
    """Mock OS desktop notification provider for testing and cross-platform isolation."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.sent_notifications: list[str] = []

    @property
    def provider_name(self) -> str:
        return "desktop_mock"

    def supports_channel(self, channel: NotificationChannelType) -> bool:
        return channel == NotificationChannelType.DESKTOP

    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        start_time = time.monotonic()
        if not self.enabled:
            return NotificationDeliveryAttempt(
                attempt_number=1,
                status=NotificationDeliveryStatus.FAILED,
                error_code="DESKTOP_DISABLED",
                error_message="Desktop notifications disabled.",
                duration_ms=(time.monotonic() - start_time) * 1000.0,
            )

        self.sent_notifications.append(notification.notification_id)
        logger.debug("Desktop popup rendered for notification id=%s", notification.notification_id)

        return NotificationDeliveryAttempt(
            attempt_number=1,
            status=NotificationDeliveryStatus.SUCCESS,
            provider_reference=f"desktop_pop_{notification.notification_id}",
            duration_ms=(time.monotonic() - start_time) * 1000.0,
        )

    async def cancel(self, notification_id: str) -> bool:
        if notification_id in self.sent_notifications:
            self.sent_notifications.remove(notification_id)
            return True
        return False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "desktop_mock",
            "supports_popups": True,
            "supports_actions": True,
        }
