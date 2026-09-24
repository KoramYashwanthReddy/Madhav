"""Services package for Module 27 — Notification System."""

from max.notifications.services.notification_service import NotificationService
from max.notifications.services.tool_integration import register_notification_tools

__all__ = ["NotificationService", "register_notification_tools"]
