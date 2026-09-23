"""Unit tests for PlanValidator and cycle detection."""

import pytest

from max.reasoning.domain import (
    CompletenessStatus,
    ConstraintClassification,
    Plan,
    PlanDependency,
    PlanStep,
    ReasoningConstraint,
)
from max.reasoning.domain.exceptions import CircularDependencyError
from max.reasoning.services import PlanValidator


def test_validator_valid_plan() -> None:
    """Test validation of a clean acyclic plan."""
    step1 = PlanStep(step_id="s1", sequence=1, title="Step 1", description="First step")
    step2 = PlanStep(
        step_id="s2", sequence=2, title="Step 2", description="Second step", dependencies=["s1"]
    )
    dep = PlanDependency(source_step_id="s1", target_step_id="s2")

    plan = Plan(
        owner_id="user_1",
        title="Clean Plan",
        description="Execute clean plan",
        steps=[step1, step2],
        dependencies=[dep],
    )

    validator = PlanValidator()
    result = validator.validate(plan)
    assert result.is_valid is True
    assert result.status == CompletenessStatus.PARTIAL
    assert len(result.errors) == 0


def test_validator_detects_circular_dependency() -> None:
    """Test that PlanValidator detects cycle and raises CircularDependencyError."""
    step1 = PlanStep(step_id="s1", sequence=1, title="Step 1", description="First")
    step2 = PlanStep(step_id="s2", sequence=2, title="Step 2", description="Second")
    step3 = PlanStep(step_id="s3", sequence=3, title="Step 3", description="Third")

    deps = [
        PlanDependency(source_step_id="s1", target_step_id="s2"),
        PlanDependency(source_step_id="s2", target_step_id="s3"),
        PlanDependency(source_step_id="s3", target_step_id="s1"),  # Cycle: s1 -> s2 -> s3 -> s1
    ]

    plan = Plan(
        owner_id="user_1",
        title="Cyclic Plan",
        description="Test cycle",
        steps=[step1, step2, step3],
        dependencies=deps,
    )

    validator = PlanValidator()
    result = validator.validate(plan)
    assert result.is_valid is False
    assert result.has_circular_dependencies is True
    assert any("Circular dependency detected" in err for err in result.errors)

    with pytest.raises(CircularDependencyError):
        validator.validate_or_raise(plan)


def test_validator_missing_prerequisite() -> None:
    """Test detection of missing dependency target step ID."""
    step1 = PlanStep(step_id="s1", sequence=1, title="Step 1", description="First")
    dep = PlanDependency(source_step_id="non_existent_step", target_step_id="s1")

    plan = Plan(
        owner_id="user_1",
        title="Dangling Plan",
        description="Test missing step",
        steps=[step1],
        dependencies=[dep],
    )

    validator = PlanValidator()
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("non_existent_step" in err for err in result.errors)


def test_validator_hard_constraint_violation() -> None:
    """Test detection of hard constraint violations."""
    step1 = PlanStep(step_id="s1", sequence=1, title="Step 1", description="Step 1 description")
    cnst = ReasoningConstraint(
        type="max_steps",
        description="0",
        classification=ConstraintClassification.HARD,
    )

    plan = Plan(
        owner_id="user_1",
        title="Violating Plan",
        description="Forbidden step count",
        steps=[step1],
        constraints=[cnst],
    )

    validator = PlanValidator()
    result = validator.validate(plan)
    assert result.is_valid is False
    assert any("Hard constraint violation" in err for err in result.errors)
