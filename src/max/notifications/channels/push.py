"""Push notification provider mock implementation."""

from __future__ import annotations

import logging
import time
from typing import Any

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt

logger = logging.getLogger(__name__)


class MockPushNotificationProvider(NotificationProvider):
    """Mock push notification provider for testing push channel integration."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    @property
    def provider_name(self) -> str:
        return "push_mock"

    def supports_channel(self, channel: NotificationChannelType) -> bool:
        return channel == NotificationChannelType.PUSH

    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        start_time = time.monotonic()
        if not self.enabled:
            return NotificationDeliveryAttempt(
                attempt_number=1,
                status=NotificationDeliveryStatus.FAILED,
                error_code="PUSH_DISABLED",
                error_message="Push notifications disabled.",
                duration_ms=(time.monotonic() - start_time) * 1000.0,
            )

        logger.debug("Push notification delivered for id=%s", notification.notification_id)
        return NotificationDeliveryAttempt(
            attempt_number=1,
            status=NotificationDeliveryStatus.SUCCESS,
            provider_reference=f"push_token_{notification.notification_id}",
            duration_ms=(time.monotonic() - start_time) * 1000.0,
        )

    async def cancel(self, notification_id: str) -> bool:
        return False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "push_mock",
            "supports_device_tokens": True,
        }
