"""Speech Notification Channel Adapter integrating Module 26 Speech System."""

from __future__ import annotations

import logging
import time
from typing import Any

from max.notifications.channels.base import NotificationProvider
from max.notifications.domain.enums import NotificationChannelType, NotificationDeliveryStatus
from max.notifications.domain.models import Notification, NotificationDeliveryAttempt
from max.speech.services.speech_service import SpeechService

logger = logging.getLogger(__name__)


class SpeechNotificationAdapter(NotificationProvider):
    """Adapter invoking Module 26 SpeechService to perform spoken notifications."""

    def __init__(self, speech_service: SpeechService | None = None, enabled: bool = True) -> None:
        self.speech_service = speech_service
        self.enabled = enabled

    @property
    def provider_name(self) -> str:
        return "speech_m26"

    def supports_channel(self, channel: NotificationChannelType) -> bool:
        return channel == NotificationChannelType.SPEECH

    async def send(self, notification: Notification) -> NotificationDeliveryAttempt:
        start_time = time.monotonic()
        if not self.enabled:
            return NotificationDeliveryAttempt(
                attempt_number=1,
                status=NotificationDeliveryStatus.FAILED,
                error_code="SPEECH_DISABLED",
                error_message="Speech notifications disabled.",
                duration_ms=(time.monotonic() - start_time) * 1000.0,
            )

        spoken_text = f"{notification.content.title}. {notification.content.body}"

        if self.speech_service is not None:
            try:
                res = await self.speech_service.synthesize(text=spoken_text)
                elapsed_ms = (time.monotonic() - start_time) * 1000.0
                return NotificationDeliveryAttempt(
                    attempt_number=1,
                    status=NotificationDeliveryStatus.SUCCESS,
                    provider_reference=res.result_id,
                    duration_ms=elapsed_ms,
                )
            except Exception as exc:
                logger.warning("Module 26 Speech synthesis failed for notification %s: %s", notification.notification_id, exc)
                return NotificationDeliveryAttempt(
                    attempt_number=1,
                    status=NotificationDeliveryStatus.FAILED,
                    error_code="M26_SPEECH_ERROR",
                    error_message=str(exc),
                    duration_ms=(time.monotonic() - start_time) * 1000.0,
                )
        else:
            # Fallback if speech_service not yet injected
            logger.info("Spoken notification (mock adapter): '%s'", spoken_text)
            return NotificationDeliveryAttempt(
                attempt_number=1,
                status=NotificationDeliveryStatus.SUCCESS,
                provider_reference=f"speech_mock_{notification.notification_id}",
                duration_ms=(time.monotonic() - start_time) * 1000.0,
            )

    async def cancel(self, notification_id: str) -> bool:
        return False

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "speech_m26",
            "module_26_integrated": self.speech_service is not None,
            "supports_tts": True,
        }
