"""Channels package for Module 27 — Notification System."""

from max.notifications.channels.base import NotificationProvider
from max.notifications.channels.desktop import MockDesktopNotificationProvider
from max.notifications.channels.email import EmailNotificationProvider
from max.notifications.channels.in_app import InAppNotificationProvider
from max.notifications.channels.push import MockPushNotificationProvider
from max.notifications.channels.registry import NotificationChannelRegistry
from max.notifications.channels.speech_adapter import SpeechNotificationAdapter

__all__ = [
    "EmailNotificationProvider",
    "InAppNotificationProvider",
    "MockDesktopNotificationProvider",
    "MockPushNotificationProvider",
    "NotificationChannelRegistry",
    "NotificationProvider",
    "SpeechNotificationAdapter",
]
