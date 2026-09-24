"""Multi-channel Notification Router for Module 27 — Notification System."""

from __future__ import annotations

import logging
from typing import Any

from max.notifications.channels.registry import NotificationChannelRegistry
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus, NotificationStatus
from max.notifications.domain.models import Notification, NotificationDelivery, NotificationDeliveryAttempt
from max.notifications.policies.policy_service import NotificationPolicyService, PolicyDecisionEnum

logger = logging.getLogger(__name__)


class NotificationRouter:
    """Routes notifications to target channel providers and manages multi-channel delivery."""

    def __init__(
        self,
        channel_registry: NotificationChannelRegistry,
        policy_service: NotificationPolicyService,
    ) -> None:
        self.registry = channel_registry
        self.policy = policy_service

    async def route_and_deliver(
        self,
        notification: Notification,
        requested_channels: list[NotificationChannelType] | None = None,
    ) -> Notification:
        """Route notification across requested or preferred channels and execute delivery."""
        channels_to_evaluate = requested_channels or [NotificationChannelType.IN_APP, NotificationChannelType.DESKTOP]

        notification.transition_to(NotificationStatus.ROUTING)
        deliveries: list[NotificationDelivery] = []

        overall_success = False

        for ch in channels_to_evaluate:
            eval_res = self.policy.evaluate_channel_policy(notification, ch)

            if eval_res.decision in (PolicyDecisionEnum.DENY, PolicyDecisionEnum.SUPPRESS):
                logger.info("Channel '%s' suppressed/denied for notification id=%s: %s", ch.value, notification.notification_id, eval_res.reason)
                continue

            # Create NotificationDelivery object
            delivery = NotificationDelivery(
                notification_id=notification.notification_id,
                channel=ch,
                status=NotificationDeliveryStatus.IN_PROGRESS,
            )

            try:
                providers = self.registry.get_providers(ch)
                provider = providers[0]
                delivery.provider_name = provider.provider_name

                attempt = await provider.send(notification)
                delivery.attempts.append(attempt)
                delivery.attempt_count = 1

                if attempt.status == NotificationDeliveryStatus.SUCCESS:
                    delivery.status = NotificationDeliveryStatus.SUCCESS
                    delivery.provider_reference = attempt.provider_reference
                    overall_success = True
                else:
                    delivery.status = NotificationDeliveryStatus.FAILED
                    delivery.last_error = attempt.error_message
            except Exception as exc:
                logger.warning("Delivery to channel '%s' failed for notification %s: %s", ch.value, notification.notification_id, exc)
                delivery.status = NotificationDeliveryStatus.FAILED
                delivery.last_error = str(exc)

            deliveries.append(delivery)

        notification.deliveries = deliveries

        if overall_success:
            notification.transition_to(NotificationStatus.DELIVERED)
        elif deliveries:
            notification.transition_to(NotificationStatus.DELIVERY_FAILED)
        else:
            notification.transition_to(NotificationStatus.SUPPRESSED)

        return notification
