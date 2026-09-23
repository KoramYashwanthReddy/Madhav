"""Unit tests for ReasoningService and providers."""

import pytest

from max.reasoning.domain import (
    ReasoningMode,
    ReasoningObjective,
    ReasoningRequest,
    ReasoningStatus,
)
from max.reasoning.domain.exceptions import ReasoningNotFoundError
from max.reasoning.providers import DevelopmentReasoningProvider
from max.reasoning.repositories import InMemoryReasoningRepository
from max.reasoning.services import ReasoningService


@pytest.mark.asyncio
async def test_development_reasoning_provider() -> None:
    """Test DevelopmentReasoningProvider output generation."""
    provider = DevelopmentReasoningProvider()
    obj = ReasoningObjective(
        title="Deploy App",
        description="Deploy web application to Kubernetes",
        desired_outcome="Application running cleanly in K8s",
    )
    req = ReasoningRequest(
        owner_id="user_1",
        objective=obj,
        mode=ReasoningMode.PLANNING,
    )

    result = await provider.reason(req, context_package=None)
    assert result.request_id == req.id
    assert result.status == ReasoningStatus.COMPLETED
    assert len(result.observations) > 0
    assert len(result.assumptions) > 0
    assert len(result.constraints) > 0
    assert result.plan is not None
    assert len(result.plan["steps"]) >= 3


@pytest.mark.asyncio
async def test_reasoning_service_lifecycle() -> None:
    """Test full reasoning service lifecycle: request creation, execution, retrieval."""
    repo = InMemoryReasoningRepository()
    provider = DevelopmentReasoningProvider()
    service = ReasoningService(
        reasoning_repository=repo,
        reasoning_provider=provider,
        context_manager=None,  # Optional context manager
    )

    obj = ReasoningObjective(
        title="Build microservice",
        description="Build Python microservice with FastAPI",
        desired_outcome="Functional microservice endpoint",
    )
    req = ReasoningRequest(
        owner_id="user_1",
        objective=obj,
        mode=ReasoningMode.DECOMPOSITION,
    )

    res = await service.execute_reasoning(req)
    assert res.status == ReasoningStatus.COMPLETED

    retrieved = await service.get_reasoning_result(res.request_id, owner_id="user_1")
    assert retrieved.request_id == res.request_id
    assert retrieved.objective_summary == obj.title

    summary = await service.get_reasoning_summary(res.request_id, owner_id="user_1")
    assert summary["status"] == "COMPLETED"
    assert "explanation" in summary

    with pytest.raises(ReasoningNotFoundError):
        await service.get_reasoning_result("invalid_id", owner_id="user_1")
