"""Rate limiting service for Module 27 — Notification System."""

from __future__ import annotations

import time
from typing import Any

from max.notifications.domain.enums import NotificationChannelType
from max.notifications.domain.models import Notification


class NotificationRateLimitService:
    """Sliding-window rate limiter preventing notification spam per user/channel."""

    def __init__(self, max_per_minute: int = 10, window_seconds: float = 60.0) -> None:
        self.max_per_minute = max_per_minute
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = {}

    def is_rate_limited(self, notification: Notification, channel: NotificationChannelType) -> bool:
        """Check if notification exceeds rate limit for (recipient, channel)."""
        key = f"{notification.recipient.recipient_id}:{channel.value}"
        now = time.monotonic()

        if key not in self._history:
            self._history[key] = []

        # Remove entries outside window
        self._history[key] = [ts for ts in self._history[key] if now - ts < self.window_seconds]

        if len(self._history[key]) >= self.max_per_minute:
            return True

        self._history[key].append(now)
        return False
