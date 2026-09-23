"""Deterministic development and testing stub model runtime implementation."""

import asyncio
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from madhav.ai.domain.capabilities import RuntimeCapabilities, RuntimeStatus
from madhav.ai.domain.enums import FinishReason, RuntimeHealthStatus, StreamEventType
from madhav.ai.domain.execution import AIExecutionMetadata
from madhav.ai.domain.requests import AIRequest
from madhav.ai.domain.responses import AIResponse, AIStreamEvent
from madhav.ai.domain.usage import AIUsage


class StubModelRuntime:
    """Deterministic development stub model runtime.

    Operates completely offline without external AI API credentials or GPU hardware.
    Exposes provider name 'stub' and model reference 'stub-development-model'.
    """

    def __init__(self, response_text: str = "Development AI runtime response.") -> None:
        self._provider_name: str = "stub"
        self._model_reference: str = "stub-development-model"
        self._response_text: str = response_text

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_reference(self) -> str:
        return self._model_reference

    async def generate(self, request: AIRequest) -> AIResponse:
        """Execute deterministic stub text generation."""
        start_mono = time.monotonic()
        started_at = datetime.now(UTC)

        # Brief async yield to simulate execution boundary
        await asyncio.sleep(0.01)

        completed_at = datetime.now(UTC)
        duration_ms = (time.monotonic() - start_mono) * 1000.0

        execution = AIExecutionMetadata(
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=round(duration_ms, 2),
            provider=self._provider_name,
            model=self._model_reference,
            request_id=request.request_id,
            stream=False,
            success=True,
        )

        return AIResponse(
            request_id=request.request_id,
            content=self._response_text,
            finish_reason=FinishReason.STOP,
            usage=AIUsage(input_tokens=10, output_tokens=5, total_tokens=15),
            execution=execution,
            model_reference=self._model_reference,
            provider=self._provider_name,
            created_at=completed_at,
        )

    async def stream(self, request: AIRequest) -> AsyncIterator[AIStreamEvent]:
        """Stream incremental deterministic stub chunks."""
        yield AIStreamEvent(
            event_type=StreamEventType.STARTED,
            content_delta=None,
            metadata={"request_id": request.request_id},
            completed=False,
        )

        words = self._response_text.split()
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.005)
            yield AIStreamEvent(
                event_type=StreamEventType.DELTA,
                content_delta=chunk,
                metadata=None,
                completed=False,
            )

        yield AIStreamEvent(
            event_type=StreamEventType.COMPLETED,
            content_delta=None,
            metadata={"request_id": request.request_id},
            completed=True,
        )

    async def health(self) -> RuntimeStatus:
        """Report operational health status for stub runtime."""
        return RuntimeStatus(
            status=RuntimeHealthStatus.AVAILABLE,
            provider=self._provider_name,
            model=self._model_reference,
            message="Stub development runtime is fully available.",
        )

    async def capabilities(self) -> RuntimeCapabilities:
        """Report capability feature set for stub runtime."""
        return RuntimeCapabilities(
            generation=True,
            streaming=True,
            token_usage=True,
            cancellation=True,
            structured_output=False,
            vision=False,
            tool_calling=False,
        )
