"""In-memory repositories for Module 27 — Notification System."""

from __future__ import annotations

import logging

from max.notifications.domain.enums import (
    NotificationCategory,
    NotificationReadState,
    NotificationSeverity,
    NotificationStatus,
)
from max.notifications.domain.exceptions import NotificationNotFoundError
from max.notifications.domain.models import (
    Notification,
    NotificationAuditEvent,
    NotificationDelivery,
    NotificationPreference,
    NotificationTemplate,
)

logger = logging.getLogger(__name__)


class MemoryNotificationRepository:
    """In-memory store for Notification entities."""

    def __init__(self) -> None:
        self._notifications: dict[str, Notification] = {}

    def save(self, notification: Notification) -> Notification:
        self._notifications[notification.notification_id] = notification
        return notification

    def get(self, notification_id: str) -> Notification:
        if notification_id not in self._notifications:
            raise NotificationNotFoundError(f"Notification '{notification_id}' not found.")
        return self._notifications[notification_id]

    def list(
        self,
        recipient_id: str | None = None,
        category: NotificationCategory | None = None,
        severity: NotificationSeverity | None = None,
        read_state: NotificationReadState | None = None,
        status: NotificationStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notification]:
        results = list(self._notifications.values())
        if recipient_id:
            results = [n for n in results if n.recipient.recipient_id == recipient_id]
        if category:
            results = [n for n in results if n.category == category]
        if severity:
            results = [n for n in results if n.severity == severity]
        if read_state:
            results = [n for n in results if n.read_state == read_state]
        if status:
            results = [n for n in results if n.status == status]

        # Sort newest first
        results.sort(key=lambda n: n.created_at, reverse=True)
        return results[offset : offset + limit]

    def count_unread(self, recipient_id: str = "user_default") -> int:
        return sum(
            1 for n in self._notifications.values()
            if n.recipient.recipient_id == recipient_id and n.read_state == NotificationReadState.UNREAD
        )

    def delete(self, notification_id: str) -> bool:
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False

    def clear(self) -> None:
        self._notifications.clear()


class MemoryNotificationDeliveryRepository:
    """In-memory store for NotificationDelivery tracking objects."""

    def __init__(self) -> None:
        self._deliveries: dict[str, NotificationDelivery] = {}

    def save(self, delivery: NotificationDelivery) -> NotificationDelivery:
        self._deliveries[delivery.delivery_id] = delivery
        return delivery

    def get(self, delivery_id: str) -> NotificationDelivery:
        if delivery_id not in self._deliveries:
            raise NotificationNotFoundError(f"NotificationDelivery '{delivery_id}' not found.")
        return self._deliveries[delivery_id]

    def list_by_notification(self, notification_id: str) -> list[NotificationDelivery]:
        return [d for d in self._deliveries.values() if d.notification_id == notification_id]

    def clear(self) -> None:
        self._deliveries.clear()


class MemoryNotificationPreferenceRepository:
    """In-memory store for user NotificationPreference objects."""

    def __init__(self) -> None:
        self._preferences: dict[str, NotificationPreference] = {}

    def get_by_user(self, user_id: str = "user_default") -> NotificationPreference:
        if user_id not in self._preferences:
            self._preferences[user_id] = NotificationPreference(user_id=user_id)
        return self._preferences[user_id]

    def save(self, preference: NotificationPreference) -> NotificationPreference:
        self._preferences[preference.user_id] = preference
        return preference

    def clear(self) -> None:
        self._preferences.clear()


class MemoryNotificationTemplateRepository:
    """In-memory store for NotificationTemplate objects."""

    def __init__(self) -> None:
        self._templates: dict[str, NotificationTemplate] = {
            "TASK_COMPLETED": NotificationTemplate(
                template_id="ntpl_task_completed",
                name="TASK_COMPLETED",
                category=NotificationCategory.TASK,
                title_template="Task Completed",
                body_template="Task {task_name} finished successfully.",
                variables=["task_name"],
            ),
            "BUILD_FAILED": NotificationTemplate(
                template_id="ntpl_build_failed",
                name="BUILD_FAILED",
                category=NotificationCategory.DEVELOPER,
                title_template="Build Failed",
                body_template="Build for {project_name} failed: {error_summary}",
                variables=["project_name", "error_summary"],
            ),
        }

    def get_by_name(self, name: str) -> NotificationTemplate:
        if name not in self._templates:
            raise NotificationNotFoundError(f"NotificationTemplate '{name}' not found.")
        return self._templates[name]

    def save(self, template: NotificationTemplate) -> NotificationTemplate:
        self._templates[template.name] = template
        return template

    def list_templates(self) -> list[NotificationTemplate]:
        return list(self._templates.values())

    def clear(self) -> None:
        self._templates.clear()


class MemoryNotificationAuditRepository:
    """In-memory store for NotificationAuditEvent log records."""

    def __init__(self) -> None:
        self._events: list[NotificationAuditEvent] = []

    def save(self, event: NotificationAuditEvent) -> NotificationAuditEvent:
        self._events.append(event)
        return event

    def list_events(self, notification_id: str | None = None, limit: int = 100) -> list[NotificationAuditEvent]:
        if notification_id:
            res = [e for e in self._events if e.notification_id == notification_id]
        else:
            res = list(self._events)
        res.sort(key=lambda e: e.timestamp, reverse=True)
        return res[:limit]

    def clear(self) -> None:
        self._events.clear()
