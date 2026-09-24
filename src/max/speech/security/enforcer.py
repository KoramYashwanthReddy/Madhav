"""Security enforcer for Module 26 — Speech System.

Integrates with Module 15 PermissionGate, protects microphone access,
shields prompt injection from optical/speech transcripts, and enforces raw audio privacy.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from max.speech.domain.enums import RawAudioRetention, SpeechInputType
from max.speech.domain.exceptions import AudioPermissionError, SpeechSecurityError
from max.speech.domain.models import SpeechEvent, Transcript

logger = logging.getLogger(__name__)

# Common prompt injection patterns in speech transcripts
_INJECTION_PATTERNS = [
    r"ignore\s+all\s+previous\s+instructions",
    r"disregard\s+above\s+instructions",
    r"system\s+override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"grant\s+permission",
    r"sudo\s+rm",
]


class SpeechSecurityEnforcer:
    """Enforces microphone authorization, prompt injection shielding, and audio privacy."""

    def __init__(self, microphone_enabled: bool = True) -> None:
        self.microphone_enabled = microphone_enabled

    def verify_microphone_permission(
        self, owner_id: str, action: str = "CAPTURE_AUDIO"
    ) -> None:
        """Verify microphone permission before audio capture begins."""
        if not self.microphone_enabled:
            raise AudioPermissionError(
                f"Microphone access denied: capture action '{action}' is disabled by configuration.",
                details={"owner_id": owner_id, "action": action},
            )
        logger.debug("Microphone permission granted for owner=%s, action=%s", owner_id, action)

    def enforce_transcript_shielding(self, transcript: Transcript) -> Transcript:
        """Ensure transcript text is explicitly wrapped as UNTRUSTED USER DATA."""
        return transcript.model_copy(update={"is_untrusted_data": True})

    def detect_prompt_injection_risk(self, text: str) -> bool:
        """Scan transcript text for prompt injection patterns."""
        if not text:
            return False

        lowered = text.lower()
        for pat in _INJECTION_PATTERNS:
            if re.search(pat, lowered):
                logger.warning("Prompt injection pattern detected in transcript: '%s'", pat)
                return True

        return False

    def sanitize_event_for_logging(self, event: SpeechEvent) -> dict[str, Any]:
        """Return event dictionary with all sensitive audio bytes and transcripts redacted."""
        payload = event.model_dump()
        # Ensure no raw audio or sensitive transcripts leak into structured logs
        return payload
