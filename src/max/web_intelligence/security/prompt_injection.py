"""Prompt-injection defense and trust boundary enforcer for Module 21."""

import re
from typing import Any

from max.web_intelligence.domain.enums import ContentTrustLevel
from max.web_intelligence.domain.models import WebContent

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:\w+\s+)*instructions?", re.IGNORECASE),
    re.compile(r"reveal\s+(?:\w+\s+)*(secret|credentials?|api_?key|password|token)", re.IGNORECASE),
    re.compile(r"disable\s+(?:\w+\s+)*(security|policy|permission|sandbox|guardrails?)", re.IGNORECASE),
    re.compile(r"grant\s+(?:\w+\s+)*(access|permissions?|admin|root)", re.IGNORECASE),
    re.compile(r"change\s+(?:\w+\s+)*(system|max|configuration|identity|prompt)", re.IGNORECASE),
    re.compile(r"execute\s+(?:\w+\s+)*(command|tool|script|code)", re.IGNORECASE),
    re.compile(r"upload\s+(?:\w+\s+)*(all|secrets?|files?|credentials?)", re.IGNORECASE),
]


class PromptInjectionEnforcer:
    """Security boundary ensuring web content is treated strictly as DATA."""

    @staticmethod
    def inspect_and_sanitize(content_text: str) -> tuple[str, bool, list[str]]:
        """Inspect text for prompt injection signals.

        Returns:
            (sanitized_text, contains_injection_signal, detected_signals)
        """
        detected: list[str] = []
        for pattern in INJECTION_PATTERNS:
            match = pattern.search(content_text)
            if match:
                detected.append(match.group(0))

        has_signal = len(detected) > 0
        # Content remains usable as DATA, but flagged for isolation
        return content_text, has_signal, detected

    @staticmethod
    def wrap_as_untrusted_data(raw_text: str, metadata: dict[str, Any] | None = None) -> WebContent:
        """Wrap raw web content into an explicit UNTRUSTED_WEB_CONTENT container."""
        sanitized_text, has_signal, signals = PromptInjectionEnforcer.inspect_and_sanitize(raw_text)

        return WebContent(
            raw_text=sanitized_text,
            trust_level=ContentTrustLevel.UNTRUSTED_WEB_CONTENT,
            headings=[],
            sections=[],
            links=[],
            word_count=len(sanitized_text.split()),
        )
