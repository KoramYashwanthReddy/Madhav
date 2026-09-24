"""Module 27 — Notification System.

Provides provider-neutral notification creation, classification, priority routing,
multi-channel delivery, deduplication, grouping, quiet hours, rate limiting,
secret redaction, and speech/API integration for Max Personal AI.
"""

from max.notifications.container import (
    NotificationContainer,
    get_notification_container,
    reset_notification_container,
)
from max.notifications.services.notification_service import NotificationService

__all__ = [
    "NotificationContainer",
    "NotificationService",
    "get_notification_container",
    "reset_notification_container",
]
