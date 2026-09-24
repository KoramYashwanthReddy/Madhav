"""Abstract base class for Notification channel providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from max.notifications.domain.enums import NotificationChannelType
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt


class NotificationProvider(ABC):
    """Provider-neutral Notification channel provider interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return canonical provider identifier."""

    @abstractmethod
    def supports_channel(self, channel: NotificationChannelType) -> bool:
        """Check if provider supports the target notification channel."""

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        """Send notification via this channel provider."""

    @abstractmethod
    async def cancel(self, notification_id: str) -> bool:
        """Cancel an in-flight or active notification on this provider."""

    @abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """Return provider capabilities dictionary."""
