"""NotificationService facade — master orchestrator for Module 27 — Notification System.

NotificationService is the single entry point for all notification operations:
callers (agents, tools, tasks, API routes) use this service.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from max.config.sections import NotificationSettings
from max.notifications.deduplication.dedup_service import NotificationDeduplicationService
from max.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannelType,
    NotificationEventType,
    NotificationPriority,
    NotificationReadState,
    NotificationSensitivity,
    NotificationSeverity,
    NotificationSourceType,
    NotificationStatus,
)
from max.notifications.domain.models import (
    Notification,
    NotificationAction,
    NotificationAuditEvent,
    NotificationContent,
    NotificationPreference,
    NotificationRecipient,
    NotificationScheduleReference,
    NotificationSource,
)
from max.notifications.grouping.grouping_service import NotificationGroupingService
from max.notifications.policies.policy_service import NotificationPolicyService
from max.notifications.preferences.preference_service import NotificationPreferenceService
from max.notifications.rate_limiting.rate_limit_service import NotificationRateLimitService
from max.notifications.repositories.repositories import (
    MemoryNotificationAuditRepository,
    MemoryNotificationDeliveryRepository,
    MemoryNotificationRepository,
    MemoryNotificationTemplateRepository,
)
from max.notifications.retry.retry_service import NotificationRetryService
from max.notifications.routing.router import NotificationRouter
from max.notifications.security.sensitivity_service import NotificationSensitivityService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationService:
    """Master facade service orchestrating the full Notification System pipeline."""

    def __init__(
        self,
        settings: NotificationSettings,
        repository: MemoryNotificationRepository,
        delivery_repository: MemoryNotificationDeliveryRepository,
        preference_service: NotificationPreferenceService,
        policy_service: NotificationPolicyService,
        router: NotificationRouter,
        dedup_service: NotificationDeduplicationService,
        grouping_service: NotificationGroupingService,
        rate_limit_service: NotificationRateLimitService,
        sensitivity_service: NotificationSensitivityService,
        retry_service: NotificationRetryService,
        audit_repository: MemoryNotificationAuditRepository,
        template_repository: MemoryNotificationTemplateRepository,
    ) -> None:
        self._settings = settings
        self._repo = repository
        self._delivery_repo = delivery_repository
        self._pref_service = preference_service
        self._policy_service = policy_service
        self._router = router
        self._dedup_service = dedup_service
        self._grouping_service = grouping_service
        self._rate_limit_service = rate_limit_service
        self._sensitivity_service = sensitivity_service
        self._retry_service = retry_service
        self._audit_repo = audit_repository
        self._template_repo = template_repository

    async def send_notification(
        self,
        title: str,
        body: str,
        recipient_id: str = "user_default",
        category: NotificationCategory = NotificationCategory.INFO,
        severity: NotificationSeverity = NotificationSeverity.NORMAL,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        sensitivity: NotificationSensitivity = NotificationSensitivity.INTERNAL,
        source_type: NotificationSourceType = NotificationSourceType.SYSTEM,
        source_id: str = "system",
        channels: list[NotificationChannelType] | None = None,
        actions: list[NotificationAction] | None = None,
        deduplication_key: str | None = None,
        group_key: str | None = None,
        schedule_reference: NotificationScheduleReference | None = None,
    ) -> Notification:
        """Create, inspect, sanitize, route, and deliver a notification."""
        # 1. Sanitize content (redact secrets)
        raw_content = NotificationContent(title=title, body=body, is_untrusted_data=True)
        sanitized_content = self._sensitivity_service.sanitize_content(raw_content)

        # 2. Build Notification entity
        notification = Notification(
            recipient=NotificationRecipient(recipient_id=recipient_id),
            source=NotificationSource(source_type=source_type, source_id=source_id),
            content=sanitized_content,
            category=category,
            severity=severity,
            priority=priority,
            sensitivity=sensitivity,
            actions=actions or [],
            deduplication_key=deduplication_key,
            schedule_reference=schedule_reference,
            status=NotificationStatus.CREATED,
        )

        # Save initial notification entity
        self._repo.save(notification)
        self._audit(notification.notification_id, NotificationEventType.NOTIFICATION_CREATED)

        # 3. Deduplication check
        if self._settings.dedup_enabled and self._dedup_service.is_duplicate(notification):
            notification.transition_to(NotificationStatus.SUPPRESSED)
            self._repo.save(notification)
            self._audit(notification.notification_id, NotificationEventType.NOTIFICATION_DEDUPLICATED)
            logger.info("Notification id=%s suppressed by deduplication.", notification.notification_id)
            return notification

        # 4. Grouping check
        if self._settings.grouping_enabled and group_key:
            grp = self._grouping_service.add_to_group(notification, group_key)
            notification.group_id = grp.group_id
            self._audit(notification.notification_id, NotificationEventType.NOTIFICATION_GROUPED)

        # 5. Route & Deliver
        target_channels = channels or [NotificationChannelType.IN_APP, NotificationChannelType.DESKTOP]

        # Filter out rate-limited channels
        allowed_channels: list[NotificationChannelType] = []
        for ch in target_channels:
            if self._settings.rate_limit_enabled and self._rate_limit_service.is_rate_limited(notification, ch):
                self._audit(notification.notification_id, NotificationEventType.NOTIFICATION_RATE_LIMITED, channel=ch)
                logger.warning("Channel '%s' rate-limited for notification id=%s", ch.value, notification.notification_id)
            else:
                allowed_channels.append(ch)

        if not allowed_channels:
            notification.transition_to(NotificationStatus.SUPPRESSED)
            self._repo.save(notification)
            return notification

        delivered_notification = await self._router.route_and_deliver(notification, allowed_channels)

        # Persist deliveries & final status
        for d in delivered_notification.deliveries:
            self._delivery_repo.save(d)

        self._repo.save(delivered_notification)
        self._audit(delivered_notification.notification_id, NotificationEventType.NOTIFICATION_DELIVERED, status=delivered_notification.status.value)

        return delivered_notification

    def mark_as_read(self, notification_id: str) -> Notification:
        """Mark notification as READ."""
        notification = self._repo.get(notification_id)
        notification.read_state = NotificationReadState.READ
        notification.read_at = _utc_now()
        if notification.status == NotificationStatus.DELIVERED:
            notification.transition_to(NotificationStatus.READ)
        self._repo.save(notification)
        self._audit(notification_id, NotificationEventType.NOTIFICATION_READ)
        return notification

    def acknowledge(self, notification_id: str, note: str | None = None) -> Notification:
        """Mark notification as ACKNOWLEDGED."""
        notification = self._repo.get(notification_id)
        notification.read_state = NotificationReadState.ACKNOWLEDGED
        notification.acknowledged_at = _utc_now()
        if notification.status in (NotificationStatus.DELIVERED, NotificationStatus.READ):
            notification.transition_to(NotificationStatus.ACKNOWLEDGED)
        self._repo.save(notification)
        self._audit(notification_id, NotificationEventType.NOTIFICATION_ACKNOWLEDGED)
        return notification

    def dismiss(self, notification_id: str) -> Notification:
        """Dismiss notification."""
        notification = self._repo.get(notification_id)
        notification.read_state = NotificationReadState.DISMISSED
        self._repo.save(notification)
        return notification

    async def cancel_notification(self, notification_id: str) -> Notification:
        """Cancel a notification."""
        notification = self._repo.get(notification_id)
        if notification.status not in (NotificationStatus.ACKNOWLEDGED, NotificationStatus.EXPIRED, NotificationStatus.CANCELLED):
            notification.transition_to(NotificationStatus.CANCELLED)
            self._repo.save(notification)
            self._audit(notification_id, NotificationEventType.NOTIFICATION_CANCELLED)
        return notification

    def list_notifications(
        self,
        recipient_id: str = "user_default",
        category: NotificationCategory | None = None,
        severity: NotificationSeverity | None = None,
        read_state: NotificationReadState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications for recipient with filters."""
        return self._repo.list(
            recipient_id=recipient_id,
            category=category,
            severity=severity,
            read_state=read_state,
            limit=limit,
            offset=offset,
        )

    def count_unread(self, recipient_id: str = "user_default") -> int:
        """Count unread notifications for recipient."""
        return self._repo.count_unread(recipient_id)

    def get_preferences(self, user_id: str = "user_default") -> NotificationPreference:
        """Get user preferences."""
        return self._pref_service.get_preferences(user_id)

    def update_preferences(self, user_id: str = "user_default", **updates: Any) -> NotificationPreference:
        """Update user preferences."""
        return self._pref_service.update_preferences(user_id, **updates)

    def _audit(
        self,
        notification_id: str,
        event_type: NotificationEventType,
        channel: NotificationChannelType | None = None,
        status: str | None = None,
    ) -> None:
        """Log audit event without recording secret bytes or body content."""
        event = NotificationAuditEvent(
            notification_id=notification_id,
            event_type=event_type,
            channel=channel,
            status=status,
        )
        self._audit_repo.save(event)
