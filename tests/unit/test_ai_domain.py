"""Unit tests for AI Runtime domain models and validation."""

import pytest

from max.ai.domain.capabilities import RuntimeCapabilities, RuntimeStatus
from max.ai.domain.enums import AIRole, RuntimeHealthStatus
from max.ai.domain.messages import AIMessage
from max.ai.domain.parameters import GenerationParameters
from max.ai.domain.requests import AIRequest
from max.ai.domain.usage import AIUsage


def test_ai_message_validation() -> None:
    """Verify AIMessage creation and empty content validation."""
    msg = AIMessage(role=AIRole.USER, content="Hello Max")
    assert msg.role == AIRole.USER
    assert msg.content == "Hello Max"

    with pytest.raises(ValueError) as exc_info:
        AIMessage(role=AIRole.USER, content="   ")
    assert "Message content cannot be empty" in str(exc_info.value)


def test_generation_parameters_validation() -> None:
    """Verify GenerationParameters range constraints."""
    params = GenerationParameters(temperature=0.7, top_p=0.9, max_tokens=512)
    assert params.temperature == 0.7
    assert params.top_p == 0.9
    assert params.max_tokens == 512

    with pytest.raises(ValueError):
        GenerationParameters(temperature=2.5)

    with pytest.raises(ValueError):
        GenerationParameters(top_p=-0.1)

    with pytest.raises(ValueError):
        GenerationParameters(max_tokens=0)


def test_ai_request_validation() -> None:
    """Verify AIRequest messages list validation."""
    req = AIRequest(messages=[AIMessage(role=AIRole.USER, content="Test")])
    assert len(req.messages) == 1
    assert len(req.request_id) > 0

    with pytest.raises(ValueError) as exc_info:
        AIRequest(messages=[])
    assert "must contain at least one message" in str(exc_info.value)


def test_ai_usage_and_execution_metadata() -> None:
    """Verify AIUsage and AIExecutionMetadata objects."""
    usage = AIUsage(input_tokens=10, output_tokens=20, total_tokens=30)
    assert usage.input_tokens == 10
    assert usage.total_tokens == 30

    unknown_usage = AIUsage()
    assert unknown_usage.input_tokens is None

    capabilities = RuntimeCapabilities(generation=True, streaming=True)
    assert capabilities.generation is True
    assert capabilities.vision is False

    status = RuntimeStatus(
        status=RuntimeHealthStatus.AVAILABLE,
        provider="stub",
        model="stub-development-model",
    )
    assert status.status == RuntimeHealthStatus.AVAILABLE
