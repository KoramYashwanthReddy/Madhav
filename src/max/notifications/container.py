"""Dependency Injection container for Module 27 — Notification System."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.notifications.channels.desktop import MockDesktopNotificationProvider
from max.notifications.channels.email import EmailNotificationProvider
from max.notifications.channels.in_app import InAppNotificationProvider
from max.notifications.channels.push import MockPushNotificationProvider
from max.notifications.channels.registry import NotificationChannelRegistry
from max.notifications.channels.speech_adapter import SpeechNotificationAdapter
from max.notifications.deduplication.dedup_service import NotificationDeduplicationService
from max.notifications.domain.enums import NotificationChannelType
from max.notifications.grouping.grouping_service import NotificationGroupingService
from max.notifications.policies.policy_service import NotificationPolicyService
from max.notifications.preferences.preference_service import NotificationPreferenceService
from max.notifications.rate_limiting.rate_limit_service import NotificationRateLimitService
from max.notifications.repositories.repositories import (
    MemoryNotificationAuditRepository,
    MemoryNotificationDeliveryRepository,
    MemoryNotificationPreferenceRepository,
    MemoryNotificationRepository,
    MemoryNotificationTemplateRepository,
)
from max.notifications.retry.retry_service import NotificationRetryService
from max.notifications.routing.router import NotificationRouter
from max.notifications.security.sensitivity_service import NotificationSensitivityService
from max.notifications.services.notification_service import NotificationService
from max.notifications.services.tool_integration import register_notification_tools
from max.speech.container import get_speech_container

logger = logging.getLogger(__name__)


class NotificationContainer:
    """Dependency Injection container managing components of Module 27 — Notification System."""

    def __init__(self) -> None:
        self.settings = get_settings().notification

        # Repositories
        self.repository = MemoryNotificationRepository()
        self.delivery_repository = MemoryNotificationDeliveryRepository()
        self.preference_repository = MemoryNotificationPreferenceRepository()
        self.template_repository = MemoryNotificationTemplateRepository()
        self.audit_repository = MemoryNotificationAuditRepository()

        # Services
        self.preference_service = NotificationPreferenceService(self.preference_repository)
        self.policy_service = NotificationPolicyService(self.preference_service)
        self.dedup_service = NotificationDeduplicationService()
        self.grouping_service = NotificationGroupingService()
        self.rate_limit_service = NotificationRateLimitService()
        self.sensitivity_service = NotificationSensitivityService()
        self.retry_service = NotificationRetryService(max_retries=self.settings.max_retries)

        # Channel Registry & Providers
        self.channel_registry = NotificationChannelRegistry()

        # Providers
        self.in_app_provider = InAppNotificationProvider(self.repository)
        self.email_provider = EmailNotificationProvider(smtp_enabled=self.settings.email_enabled)
        self.desktop_provider = MockDesktopNotificationProvider(enabled=self.settings.desktop_enabled)
        self.push_provider = MockPushNotificationProvider(enabled=self.settings.push_enabled)

        # Module 26 Speech Service Integration
        speech_svc = None
        try:
            speech_container = get_speech_container()
            speech_svc = speech_container.service
        except Exception as exc:
            logger.debug("SpeechService injection deferred or unavailable: %s", exc)

        self.speech_adapter = SpeechNotificationAdapter(
            speech_service=speech_svc, enabled=self.settings.speech_enabled
        )

        # Register providers to channels
        self.channel_registry.register(NotificationChannelType.IN_APP, self.in_app_provider)
        self.channel_registry.register(NotificationChannelType.EMAIL, self.email_provider)
        self.channel_registry.register(NotificationChannelType.DESKTOP, self.desktop_provider)
        self.channel_registry.register(NotificationChannelType.PUSH, self.push_provider)
        self.channel_registry.register(NotificationChannelType.SPEECH, self.speech_adapter)

        # Notification Router
        self.router = NotificationRouter(
            channel_registry=self.channel_registry,
            policy_service=self.policy_service,
        )

        # Master Facade Service
        self.service = NotificationService(
            settings=self.settings,
            repository=self.repository,
            delivery_repository=self.delivery_repository,
            preference_service=self.preference_service,
            policy_service=self.policy_service,
            router=self.router,
            dedup_service=self.dedup_service,
            grouping_service=self.grouping_service,
            rate_limit_service=self.rate_limit_service,
            sensitivity_service=self.sensitivity_service,
            retry_service=self.retry_service,
            audit_repository=self.audit_repository,
            template_repository=self.template_repository,
        )

        # Tool Registration with M14 Tool Registry
        try:
            from max.tools.services.registry import ToolRegistryService
            register_notification_tools(ToolRegistryService())
        except Exception as exc:
            logger.debug("M14 ToolRegistry auto-registration deferred or skipped: %s", exc)


_NOTIFICATION_CONTAINER_INSTANCE: NotificationContainer | None = None


def get_notification_container() -> NotificationContainer:
    """Get global NotificationContainer singleton instance."""
    global _NOTIFICATION_CONTAINER_INSTANCE
    if _NOTIFICATION_CONTAINER_INSTANCE is None:
        _NOTIFICATION_CONTAINER_INSTANCE = NotificationContainer()
    return _NOTIFICATION_CONTAINER_INSTANCE


def reset_notification_container() -> None:
    """Reset global NotificationContainer instance for test isolation."""
    global _NOTIFICATION_CONTAINER_INSTANCE
    _NOTIFICATION_CONTAINER_INSTANCE = None
