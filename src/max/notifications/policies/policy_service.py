"""Policy evaluation service for Module 27 — Notification System."""

from __future__ import annotations

import logging
from enum import StrEnum

from pydantic import BaseModel, Field

from max.notifications.domain.enums import (
    NotificationChannelType,
    NotificationSensitivity,
)
from max.notifications.domain.models import Notification, NotificationPreference
from max.notifications.preferences.preference_service import NotificationPreferenceService

logger = logging.getLogger(__name__)


class PolicyDecisionEnum(StrEnum):
    """Possible policy decisions."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    SUPPRESS = "SUPPRESS"
    QUEUE = "QUEUE"
    ROUTE_ALTERNATIVE = "ROUTE_ALTERNATIVE"


class PolicyEvaluationResult(BaseModel):
    """Result of policy evaluation for a specific channel."""

    decision: PolicyDecisionEnum = Field(default=PolicyDecisionEnum.ALLOW)
    channel: NotificationChannelType
    reason: str = Field(default="Permitted by policy")


class NotificationPolicyService:
    """Evaluates notification safety policies, sensitivity limits, and preferences."""

    def __init__(self, preference_service: NotificationPreferenceService) -> None:
        self._pref_service = preference_service

    def evaluate_channel_policy(
        self,
        notification: Notification,
        channel: NotificationChannelType,
        preference: NotificationPreference | None = None,
    ) -> PolicyEvaluationResult:
        """Evaluate policy hierarchy for a single notification on a specific channel."""
        pref = preference or self._pref_service.get_preferences(notification.recipient.recipient_id)

        # 1. Sensitivity channel restriction check
        if notification.sensitivity in (NotificationSensitivity.SENSITIVE, NotificationSensitivity.HIGHLY_SENSITIVE):
            # Highly sensitive notifications blocked on public channels (DESKTOP popups, SPEECH output) unless explicit
            if channel in (NotificationChannelType.SPEECH, NotificationChannelType.DESKTOP) and notification.sensitivity == NotificationSensitivity.HIGHLY_SENSITIVE:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.DENY,
                    channel=channel,
                    reason=f"Channel '{channel.value}' blocked for HIGHLY_SENSITIVE content protection.",
                )

        # 2. Preference evaluation
        permitted, reason = self._pref_service.is_channel_permitted(
            pref, channel, notification.severity, notification.category
        )

        if not permitted:
            if "Quiet hours" in reason:
                return PolicyEvaluationResult(
                    decision=PolicyDecisionEnum.QUEUE, channel=channel, reason=reason
                )
            return PolicyEvaluationResult(
                decision=PolicyDecisionEnum.SUPPRESS, channel=channel, reason=reason
            )

        return PolicyEvaluationResult(
            decision=PolicyDecisionEnum.ALLOW, channel=channel, reason="Permitted."
        )
