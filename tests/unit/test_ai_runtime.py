"""Unit tests for Module 04 AI Runtime components."""

import asyncio
from unittest.mock import MagicMock

import pytest

from madhav.ai.domain.enums import AIRole, FinishReason, RuntimeHealthStatus
from madhav.ai.domain.messages import AIMessage
from madhav.ai.domain.requests import AIRequest
from madhav.ai.domain.responses import AIResponse
from madhav.ai.exceptions import (
    AIInferenceCancelledError,
    AIInferenceTimeoutError,
    AIRuntimeError,
    AIRuntimeUnavailableError,
)
from madhav.ai.runtime.manager import AIRuntimeManager
from madhav.ai.runtime.registry import RuntimeRegistry
from madhav.ai.runtime.stub import StubModelRuntime


class TestStubModelRuntime:
    """Tests for StubModelRuntime."""

    @pytest.mark.asyncio
    async def test_stub_generate_success(self) -> None:
        runtime = StubModelRuntime()
        request = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Hello Madhav")])
        response = await runtime.generate(request)

        assert isinstance(response, AIResponse)
        assert response.request_id == request.request_id
        assert "Development AI runtime response" in response.content
        assert response.finish_reason == FinishReason.STOP
        assert response.provider == "stub"
        assert response.model_reference == "stub-development-model"
        assert response.usage is not None
        assert response.usage.input_tokens is not None
        assert response.usage.output_tokens is not None
        assert response.execution.success is True

    @pytest.mark.asyncio
    async def test_stub_health_and_capabilities(self) -> None:
        runtime = StubModelRuntime()
        health = await runtime.health()
        assert health.status == RuntimeHealthStatus.AVAILABLE
        assert health.provider == "stub"

        caps = await runtime.capabilities()
        assert caps.generation is True
        assert caps.streaming is True
        assert caps.token_usage is True
        assert caps.vision is False


class TestRuntimeRegistry:
    """Tests for RuntimeRegistry."""

    def test_register_and_resolve(self) -> None:
        registry = RuntimeRegistry()
        stub = StubModelRuntime()
        registry.register("stub", stub)

        assert registry.resolve("stub") is stub
        assert registry.has_provider("stub") is True
        assert "stub" in registry.list_providers()

    def test_resolve_unregistered_raises_error(self) -> None:
        registry = RuntimeRegistry()
        with pytest.raises(AIRuntimeUnavailableError, match="No AI runtime registered"):
            registry.resolve("nonexistent")

    def test_unregister(self) -> None:
        registry = RuntimeRegistry()
        stub = StubModelRuntime()
        registry.register("stub", stub)

        assert registry.unregister("stub") is True
        assert registry.has_provider("stub") is False
        assert registry.unregister("stub") is False


class TestAIRuntimeManager:
    """Tests for AIRuntimeManager execution flow, timeouts, and cancellation."""

    @pytest.mark.asyncio
    async def test_manager_generate_default_provider(self) -> None:
        registry = RuntimeRegistry()
        stub = StubModelRuntime()
        registry.register("stub", stub)

        manager = AIRuntimeManager(registry=registry, default_provider="stub", default_timeout=5.0)
        request = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Test request")])

        response = await manager.generate(request)
        assert response.provider == "stub"
        assert response.execution.success is True
        assert response.execution.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_manager_timeout_handling(self) -> None:
        slow_runtime = MagicMock()
        slow_runtime.provider_name = "slow"
        slow_runtime.model_reference = "slow-model"

        async def slow_generate(request: AIRequest) -> AIResponse:
            await asyncio.sleep(0.5)
            return MagicMock(spec=AIResponse)

        slow_runtime.generate.side_effect = slow_generate

        registry = RuntimeRegistry()
        registry.register("slow", slow_runtime)

        manager = AIRuntimeManager(registry=registry, default_provider="slow", default_timeout=0.05)
        request = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Slow prompt")])

        with pytest.raises(AIInferenceTimeoutError) as exc_info:
            await manager.generate(request)

        assert "timed out after 0.05" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manager_cancellation_handling(self) -> None:
        cancelled_runtime = MagicMock()
        cancelled_runtime.provider_name = "cancelled"
        cancelled_runtime.model_reference = "cancelled-model"

        async def cancelling_generate(request: AIRequest) -> AIResponse:
            raise asyncio.CancelledError()

        cancelled_runtime.generate.side_effect = cancelling_generate

        registry = RuntimeRegistry()
        registry.register("cancelled", cancelled_runtime)

        manager = AIRuntimeManager(
            registry=registry, default_provider="cancelled", default_timeout=5.0
        )
        request = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Cancelled prompt")])

        with pytest.raises(AIInferenceCancelledError):
            await manager.generate(request)

    @pytest.mark.asyncio
    async def test_manager_unhandled_exception_mapping(self) -> None:
        failing_runtime = MagicMock()
        failing_runtime.provider_name = "failing"
        failing_runtime.model_reference = "failing-model"

        async def failing_generate(request: AIRequest) -> AIResponse:
            raise ValueError("Unexpected internal runtime failure")

        failing_runtime.generate.side_effect = failing_generate

        registry = RuntimeRegistry()
        registry.register("failing", failing_runtime)

        manager = AIRuntimeManager(
            registry=registry, default_provider="failing", default_timeout=5.0
        )
        request = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Failing prompt")])

        with pytest.raises(AIRuntimeError) as exc_info:
            await manager.generate(request)

        assert "Inference failed unexpectedly" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_manager_get_status_and_capabilities(self) -> None:
        registry = RuntimeRegistry()
        stub = StubModelRuntime()
        registry.register("stub", stub)

        manager = AIRuntimeManager(registry=registry, default_provider="stub")

        status = await manager.get_status()
        assert status.status == RuntimeHealthStatus.AVAILABLE

        caps = await manager.get_capabilities()
        assert caps.generation is True
