"""Unit tests for PlanService, versioning, revision, and comparison."""

import pytest

from madhav.reasoning.domain import (
    PlanStep,
)
from madhav.reasoning.domain.exceptions import PlanNotFoundError
from madhav.reasoning.repositories import (
    InMemoryPlanRepository,
    InMemoryPlanVersionRepository,
)
from madhav.reasoning.services import (
    PlanComparer,
    PlanService,
    PlanValidator,
)


@pytest.mark.asyncio
async def test_plan_service_versioning_and_revision() -> None:
    """Test plan creation, version snapshotting, revision, and version diff comparison."""
    plan_repo = InMemoryPlanRepository()
    version_repo = InMemoryPlanVersionRepository()
    validator = PlanValidator()
    comparer = PlanComparer()

    service = PlanService(
        plan_repository=plan_repo,
        version_repository=version_repo,
        validator=validator,
        comparer=comparer,
    )

    step1 = PlanStep(sequence=1, title="Initial Step", description="First step description")

    created_plan = await service.create_plan(
        owner_id="user_1",
        title="Original Plan",
        description="Achieve goal v1",
        steps=[step1],
    )
    assert created_plan.version == 1

    versions = await service.get_plan_versions(created_plan.plan_id, owner_id="user_1")
    assert len(versions) == 1
    assert versions[0].version_number == 1

    # Revise plan
    step2 = PlanStep(sequence=2, title="Second Step", description="Added in v2")
    new_steps = [step1, step2]
    revised_plan = await service.revise_plan(
        plan_id=created_plan.plan_id,
        owner_id="user_1",
        new_steps=new_steps,
        reason_for_change="Added step 2 for completeness",
    )

    assert revised_plan.version == 2
    assert len(revised_plan.steps) == 2

    versions = await service.get_plan_versions(created_plan.plan_id, owner_id="user_1")
    assert len(versions) == 2

    # Compare versions
    diff = await service.compare_versions(
        created_plan.plan_id, version_a=1, version_b=2, owner_id="user_1"
    )
    assert len(diff.added_steps) == 1
    assert "Second Step" in diff.added_steps[0]


@pytest.mark.asyncio
async def test_plan_service_not_found() -> None:
    """Test error handling when plan is not found."""
    service = PlanService(
        plan_repository=InMemoryPlanRepository(),
        version_repository=InMemoryPlanVersionRepository(),
    )
    with pytest.raises(PlanNotFoundError):
        await service.get_plan("invalid_id", owner_id="user_1")
