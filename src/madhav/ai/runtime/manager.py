"""AI Runtime manager orchestrating request execution, timeouts, and response normalization."""

import asyncio
import logging
import time

from madhav.ai.domain.capabilities import RuntimeCapabilities, RuntimeStatus
from madhav.ai.domain.requests import AIRequest
from madhav.ai.domain.responses import AIResponse
from madhav.ai.exceptions import (
    AIInferenceCancelledError,
    AIInferenceTimeoutError,
    AIResponseValidationError,
    AIRuntimeError,
    AIValidationError,
)
from madhav.ai.runtime.registry import RuntimeRegistry
from madhav.config.settings import get_settings

logger = logging.getLogger("madhav.ai.manager")


class AIRuntimeManager:
    """Core AI Runtime manager responsible for request execution and telemetry."""

    def __init__(
        self,
        registry: RuntimeRegistry | None = None,
        default_provider: str | None = None,
        default_timeout: float | None = None,
    ) -> None:
        self._registry: RuntimeRegistry = registry or RuntimeRegistry()
        self._settings = get_settings()
        self._default_provider = default_provider
        self._default_timeout = default_timeout

    @property
    def registry(self) -> RuntimeRegistry:
        """Expose runtime registry instance."""
        return self._registry

    async def generate(
        self, request: AIRequest, provider_override: str | None = None
    ) -> AIResponse:
        """Execute AI text generation request with timeout protection and response normalization."""
        # 1. Validate request parameters
        self._validate_request(request)

        # 2. Resolve target runtime adapter
        provider = provider_override or self._default_provider or self._settings.ai_runtime.provider
        runtime = self._registry.resolve_runtime(provider)

        timeout = (
            request.timeout or self._default_timeout or self._settings.ai_runtime.timeout_seconds
        )
        start_mono = time.monotonic()

        logger.info(
            "Executing AI inference request: request_id=%s provider=%s timeout=%.1fs",
            request.request_id,
            runtime.provider_name,
            timeout,
        )

        # 3. Execute inference with timeout and cancellation protection
        try:
            response = await asyncio.wait_for(
                runtime.generate(request),
                timeout=timeout,
            )
        except TimeoutError as exc:
            duration_ms = (time.monotonic() - start_mono) * 1000.0
            logger.warning(
                "AI inference timed out: request_id=%s provider=%s duration=%.2fms",
                request.request_id,
                runtime.provider_name,
                duration_ms,
            )
            raise AIInferenceTimeoutError(
                f"AI inference request '{request.request_id}' timed out after {timeout} seconds.",
                details={"request_id": request.request_id, "timeout": timeout},
            ) from exc
        except asyncio.CancelledError as exc:
            duration_ms = (time.monotonic() - start_mono) * 1000.0
            logger.warning(
                "AI inference cancelled: request_id=%s provider=%s duration=%.2fms",
                request.request_id,
                runtime.provider_name,
                duration_ms,
            )
            raise AIInferenceCancelledError(
                f"AI inference request '{request.request_id}' was cancelled.",
                details={"request_id": request.request_id},
            ) from exc
        except Exception as exc:
            logger.exception("AI inference execution failure: request_id=%s", request.request_id)
            raise AIRuntimeError(
                f"Inference failed unexpectedly: {exc!s}",
                details={"request_id": request.request_id, "provider": runtime.provider_name},
            ) from exc

        # 4. Normalize and validate response envelope
        self._validate_response(response, request.request_id)

        duration_ms = (time.monotonic() - start_mono) * 1000.0
        logger.info(
            "AI inference completed successfully: request_id=%s provider=%s duration=%.2fms",
            request.request_id,
            response.provider,
            duration_ms,
        )

        return response

    async def get_status(self, provider: str | None = None) -> RuntimeStatus:
        """Get diagnostic health status for specified runtime provider."""
        resolved_provider = provider or self._default_provider or self._settings.ai_runtime.provider
        runtime = self._registry.resolve_runtime(resolved_provider)
        return await runtime.health()

    async def get_capabilities(self, provider: str | None = None) -> RuntimeCapabilities:
        """Get capability feature matrix for specified runtime provider."""
        resolved_provider = provider or self._default_provider or self._settings.ai_runtime.provider
        runtime = self._registry.resolve_runtime(resolved_provider)
        return await runtime.capabilities()

    def _validate_request(self, request: AIRequest) -> None:
        """Perform pre-execution validation checks on AIRequest."""
        if not request.messages:
            raise AIValidationError("AI request messages list cannot be empty.")
        if request.generation.temperature < 0.0 or request.generation.temperature > 2.0:
            raise AIValidationError(
                f"Invalid temperature: {request.generation.temperature}. "
                "Must be between 0.0 and 2.0."
            )
        if request.generation.max_tokens <= 0:
            raise AIValidationError("max_tokens parameter must be a positive integer.")

    def _validate_response(self, response: AIResponse, request_id: str) -> None:
        """Perform post-execution sanity checks on AIResponse."""
        if not isinstance(response.content, str):
            raise AIResponseValidationError(
                "Generated content payload is invalid.",
                details={"request_id": request_id},
            )
        if not response.provider or not response.model_reference:
            raise AIResponseValidationError(
                "Response provider or model_reference metadata missing.",
                details={"request_id": request_id},
            )
