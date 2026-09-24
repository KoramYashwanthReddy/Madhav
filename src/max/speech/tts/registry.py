"""Provider registry for Text-To-Speech engines."""

from __future__ import annotations

import logging

from max.speech.domain.exceptions import SpeechProviderError
from max.speech.tts.base import TextToSpeechProvider

logger = logging.getLogger(__name__)


class TextToSpeechProviderRegistry:
    """Registry managing available TTS providers."""

    def __init__(self) -> None:
        self._providers: dict[str, TextToSpeechProvider] = {}
        self._default_provider: str = "mock"

    def register(self, provider: TextToSpeechProvider, set_as_default: bool = False) -> None:
        """Register a TTS provider instance."""
        name = provider.provider_name.lower()
        self._providers[name] = provider
        logger.info("Registered TTS provider: %s", name)
        if set_as_default or len(self._providers) == 1:
            self._default_provider = name

    def get(self, name: str | None = None) -> TextToSpeechProvider:
        """Retrieve registered TTS provider by name or return default."""
        target = (name or self._default_provider).lower()
        if target not in self._providers:
            raise SpeechProviderError(
                f"TTS provider '{target}' not registered. Available: {list(self._providers.keys())}."
            )
        return self._providers[target]

    def list_providers(self) -> list[str]:
        """Return list of registered TTS provider names."""
        return list(self._providers.keys())
