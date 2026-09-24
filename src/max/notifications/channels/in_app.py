"""In-App notification provider implementation."""

from __future__ import annotations

import time
from typing import Any

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt
from max.notifications.repositories.repositories import MemoryNotificationRepository


class InAppNotificationProvider(NotificationProvider):
    """In-App notification provider persisting directly to the notification repository."""

    def __init__(self, repository: MemoryNotificationRepository) -> None:
        self._repo = repository

    @property
    def provider_name(self) -> str:
        return "in_app"

    def supports_channel(self, channel: NotificationChannelType) -> bool:
        return channel == NotificationChannelType.IN_APP

    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        start_time = time.monotonic()
        # Save notification state into repository
        self._repo.save(notification)
        elapsed_ms = (time.monotonic() - start_time) * 1000.0

        return NotificationDeliveryAttempt(
            attempt_number=1,
            status=NotificationDeliveryStatus.SUCCESS,
            provider_reference=f"in_app_{notification.notification_id}",
            duration_ms=elapsed_ms,
        )

    async def cancel(self, notification_id: str) -> bool:
        return self._repo.delete(notification_id)

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "in_app",
            "supports_read_state": True,
            "supports_acknowledgement": True,
            "supports_grouping": True,
        }
