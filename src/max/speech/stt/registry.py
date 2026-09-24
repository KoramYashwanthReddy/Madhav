"""Provider registry for Speech-To-Text engines."""

from __future__ import annotations

import logging

from max.speech.domain.exceptions import SpeechProviderError
from max.speech.stt.base import SpeechToTextProvider

logger = logging.getLogger(__name__)


class SpeechToTextProviderRegistry:
    """Registry managing available STT providers."""

    def __init__(self) -> None:
        self._providers: dict[str, SpeechToTextProvider] = {}
        self._default_provider: str = "mock"

    def register(self, provider: SpeechToTextProvider, set_as_default: bool = False) -> None:
        """Register an STT provider instance."""
        name = provider.provider_name.lower()
        self._providers[name] = provider
        logger.info("Registered STT provider: %s", name)
        if set_as_default or len(self._providers) == 1:
            self._default_provider = name

    def get(self, name: str | None = None) -> SpeechToTextProvider:
        """Retrieve registered STT provider by name or return default."""
        target = (name or self._default_provider).lower()
        if target not in self._providers:
            raise SpeechProviderError(
                f"STT provider '{target}' not registered. Available: {list(self._providers.keys())}."
            )
        return self._providers[target]

    def list_providers(self) -> list[str]:
        """Return list of registered STT provider names."""
        return list(self._providers.keys())
