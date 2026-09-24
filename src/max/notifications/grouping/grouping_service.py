"""Notification grouping service for Module 27 — Notification System."""

from __future__ import annotations

import logging
from typing import Any

from max.notifications.domain.models import Notification, NotificationGroup

logger = logging.getLogger(__name__)


class NotificationGroupingService:
    """Aggregates individual notifications into structured NotificationGroup objects."""

    def __init__(self) -> None:
        self._groups: dict[str, NotificationGroup] = {}

    def get_or_create_group(self, group_key: str, default_title: str) -> NotificationGroup:
        """Retrieve or initialize NotificationGroup by group key."""
        if group_key not in self._groups:
            self._groups[group_key] = NotificationGroup(group_key=group_key, title=default_title)
        return self._groups[group_key]

    def add_to_group(self, notification: Notification, group_key: str) -> NotificationGroup:
        """Add notification ID to an aggregated notification group."""
        group = self.get_or_create_group(group_key, f"Group: {group_key}")
        if notification.notification_id not in group.member_notification_ids:
            group.member_notification_ids.append(notification.notification_id)
            group.count = len(group.member_notification_ids)
            group.title = f"{group.count} notifications for {group_key}"
        return group
