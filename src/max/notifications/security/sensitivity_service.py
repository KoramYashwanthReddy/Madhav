"""Sensitivity service and secret redaction layer for Module 27 — Notification System."""

from __future__ import annotations

import logging
import re

from max.notifications.domain.enums import NotificationChannelType, NotificationSensitivity
from max.notifications.domain.models import Notification, NotificationContent

logger = logging.getLogger(__name__)

# Common secret regex patterns (API keys, tokens, passwords)
_SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|secret|password|bearer|token)\s*[:=]\s*['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?",
    r"sk-[a-zA-Z0-9]{32,}",
    r"ghp_[a-zA-Z0-9]{36}",
]


class NotificationSensitivityService:
    """Enforces secret redaction and content sensitivity channel protection."""

    def redact_secrets(self, text: str) -> str:
        """Mask API keys, passwords, and tokens in notification text."""
        if not text:
            return ""

        redacted = text
        for pat in _SECRET_PATTERNS:
            redacted = re.sub(pat, "***REDACTED***", redacted)

        return redacted

    def sanitize_content(self, content: NotificationContent) -> NotificationContent:
        """Return NotificationContent with title and body secrets redacted."""
        redacted_title = self.redact_secrets(content.title)
        redacted_body = self.redact_secrets(content.body)

        return content.model_copy(
            update={"title": redacted_title, "body": redacted_body}
        )

    def is_channel_allowed_for_sensitivity(
        self, sensitivity: NotificationSensitivity, channel: NotificationChannelType
    ) -> bool:
        """Verify whether channel is allowed for notification sensitivity level."""
        if sensitivity == NotificationSensitivity.HIGHLY_SENSITIVE:
            # Block public popup/audio channels
            if channel in (NotificationChannelType.DESKTOP, NotificationChannelType.SPEECH, NotificationChannelType.PUSH):
                return False
        return True
