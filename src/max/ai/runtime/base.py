"""Provider-neutral model runtime interface protocol."""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from max.ai.domain.capabilities import RuntimeCapabilities, RuntimeStatus
from max.ai.domain.requests import AIRequest
from max.ai.domain.responses import AIResponse, AIStreamEvent


@runtime_checkable
class ModelRuntime(Protocol):
    """Protocol defining the provider-neutral AI model execution runtime contract."""

    @property
    def provider_name(self) -> str:
        """Return unique provider identifier string (e.g. stub, openai, local)."""
        ...

    @property
    def model_reference(self) -> str:
        """Return model reference identifier string."""
        ...

    async def generate(self, request: AIRequest) -> AIResponse:
        """Execute single-turn AI text generation inference."""
        ...

    def stream(self, request: AIRequest) -> AsyncIterator[AIStreamEvent]:
        """Stream incremental AI generation events."""
        ...

    async def health(self) -> RuntimeStatus:
        """Check runtime operational health status."""
        ...

    async def capabilities(self) -> RuntimeCapabilities:
        """Retrieve declared runtime capabilities."""
        ...
