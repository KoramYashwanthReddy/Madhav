"""Registry for Notification channel providers."""

from __future__ import annotations

import logging

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType
from max.notifications.domain.exceptions import NotificationChannelError

logger = logging.getLogger(__name__)


class NotificationChannelRegistry:
    """Registry managing available notification channel providers."""

    def __init__(self) -> None:
        self._providers: dict[NotificationChannelType, list[NotificationProvider]] = {}

    def register(self, channel: NotificationChannelType, provider: NotificationProvider) -> None:
        """Register a provider for a specific channel type."""
        if channel not in self._providers:
            self._providers[channel] = []
        self._providers[channel].append(provider)
        logger.info("Registered NotificationProvider '%s' for channel '%s'", provider.provider_name, channel.value)

    def get_providers(self, channel: NotificationChannelType) -> list[NotificationProvider]:
        """Retrieve registered providers for a channel type."""
        if channel not in self._providers or not self._providers[channel]:
            raise NotificationChannelError(
                f"No NotificationProvider registered for channel '{channel.value}'."
            )
        return self._providers[channel]

    def list_channels(self) -> list[NotificationChannelType]:
        """Return list of supported channels."""
        return list(self._providers.keys())
