"""User preference service and quiet hours evaluator for Module 27 — Notification System."""

from __future__ import annotations

from datetime import datetime, time, timezone
import logging

from max.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannelType,
    NotificationSeverity,
)
from max.notifications.domain.models import NotificationPreference
from max.notifications.repositories.repositories import MemoryNotificationPreferenceRepository

logger = logging.getLogger(__name__)


def _parse_time(time_str: str) -> time:
    """Parse 'HH:MM' string to time object."""
    try:
        parts = time_str.split(":")
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        return time(hour=22, minute=0)


class NotificationPreferenceService:
    """Manages user delivery preferences, quiet hours evaluation, and category filters."""

    def __init__(self, repository: MemoryNotificationPreferenceRepository) -> None:
        self._repo = repository

    def get_preferences(self, user_id: str = "user_default") -> NotificationPreference:
        """Retrieve user notification preferences."""
        return self._repo.get_by_user(user_id)

    def update_preferences(
        self, user_id: str = "user_default", **updates: Any
    ) -> NotificationPreference:
        """Update fields on user notification preferences."""
        pref = self.get_preferences(user_id)
        updated = pref.model_copy(update=updates)
        return self._repo.save(updated)

    def is_in_quiet_hours(
        self, pref: NotificationPreference, current_dt: datetime | None = None
    ) -> bool:
        """Evaluate if current time falls within user quiet hours window."""
        if not pref.quiet_hours_enabled:
            return False

        now = (current_dt or datetime.now(timezone.utc)).time()
        start = _parse_time(pref.quiet_hours_start)
        end = _parse_time(pref.quiet_hours_end)

        if start <= end:
            return start <= now <= end
        else:
            # Spans midnight (e.g., 22:00 -> 07:00)
            return now >= start or now <= end

    def is_channel_permitted(
        self,
        pref: NotificationPreference,
        channel: NotificationChannelType,
        severity: NotificationSeverity,
        category: NotificationCategory,
        current_dt: datetime | None = None,
    ) -> tuple[bool, str]:
        """Evaluate whether a notification is permitted for delivery on a specific channel."""
        # 1. Category check
        if category in pref.disabled_categories:
            return False, f"Category '{category.value}' is disabled in user preferences."

        # 2. Quiet hours check
        if self.is_in_quiet_hours(pref, current_dt):
            if severity == NotificationSeverity.CRITICAL and pref.allow_critical_in_quiet_hours:
                pass  # Allow CRITICAL in quiet hours
            else:
                return False, "Quiet hours active."

        # 3. Channel enabled check
        if channel not in pref.enabled_channels:
            return False, f"Channel '{channel.value}' is disabled in user preferences."

        # 4. Severity threshold check
        severity_order = {
            NotificationSeverity.LOW: 1,
            NotificationSeverity.NORMAL: 2,
            NotificationSeverity.HIGH: 3,
            NotificationSeverity.CRITICAL: 4,
        }
        if severity_order.get(severity, 1) < severity_order.get(pref.min_severity_threshold, 1):
            return False, f"Severity '{severity.value}' below user minimum threshold '{pref.min_severity_threshold.value}'."

        return True, "Permitted."
