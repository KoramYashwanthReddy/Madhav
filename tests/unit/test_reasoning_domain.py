"""Unit tests for reasoning and planning domain models."""

import pytest
from pydantic import ValidationError

from madhav.reasoning.domain import (
    ConfidenceLevel,
    ConstraintClassification,
    ConstraintType,
    MissingInformation,
    Plan,
    PlanDependency,
    PlanRisk,
    PlanStep,
    ReasoningAssumption,
    ReasoningConstraint,
    ReasoningEvidence,
    ReasoningMode,
    ReasoningObjective,
    ReasoningObservation,
    ReasoningRequest,
    RiskLevel,
)


def test_reasoning_objective_validation() -> None:
    """Test reasoning objective creation and validation."""
    obj = ReasoningObjective(
        title="Deploy App",
        description="Deploy web application to production",
        desired_outcome="Application running cleanly",
        success_criteria=["Health check passes", "Logs clear"],
        priority=1,
    )
    assert obj.title == "Deploy App"
    assert len(obj.success_criteria) == 2

    with pytest.raises(ValidationError):
        ReasoningObjective(
            title="",
            description="desc",
            desired_outcome="out",
        )


def test_reasoning_request_validation() -> None:
    """Test reasoning request validation."""
    obj = ReasoningObjective(
        title="Study Spring Boot",
        description="Learn Spring Boot framework",
        desired_outcome="Master Spring Boot microservices",
    )
    req = ReasoningRequest(
        owner_id="user_123",
        objective=obj,
        mode=ReasoningMode.PLANNING,
    )
    assert req.owner_id == "user_123"
    assert req.mode == ReasoningMode.PLANNING

    with pytest.raises((ValidationError, Exception)):
        ReasoningRequest(
            owner_id="",
            objective=obj,
        )


def test_observation_provenance() -> None:
    """Test structured observations and evidence references."""
    _ = ReasoningEvidence(
        source_type="MEMORY",
        source_id="mem_1",
        summary="User studies 5 hours daily",
    )
    obs = ReasoningObservation(
        description="User has 5 hours daily bandwidth",
        source_type="MEMORY",
        source_id="mem_1",
    )
    assert obs.source_type == "MEMORY"


def test_assumptions_and_constraints() -> None:
    """Test assumptions and constraints domain models."""
    asm = ReasoningAssumption(
        description="PostgreSQL is installed",
        confidence=ConfidenceLevel.HIGH,
    )
    assert asm.confidence == ConfidenceLevel.HIGH

    cnst = ReasoningConstraint(
        type=ConstraintType.TECHNOLOGY,
        description="Must use Docker",
        classification=ConstraintClassification.HARD,
    )
    assert cnst.classification == ConstraintClassification.HARD


def test_missing_information() -> None:
    """Test missing information representation."""
    info = MissingInformation(
        description="Target deployment URL",
        importance=ConfidenceLevel.HIGH,
        is_blocking=True,
    )
    assert info.is_blocking is True


def test_plan_step_and_plan_domain() -> None:
    """Test plan and plan step initialization."""
    step1 = PlanStep(
        step_id="step_1",
        sequence=1,
        title="Build container",
        description="Build Docker image",
        objective="Create production container image",
    )
    step2 = PlanStep(
        step_id="step_2",
        sequence=2,
        title="Deploy container",
        description="Deploy Docker image",
        objective="Run container in production",
        dependencies=["step_1"],
    )
    dep = PlanDependency(source_step_id="step_1", target_step_id="step_2")
    risk = PlanRisk(
        description="Image build failure",
        severity=RiskLevel.MEDIUM,
        affected_step_id="step_1",
    )
    plan = Plan(
        owner_id="user_123",
        title="Deployment Plan",
        description="Deploy app",
        steps=[step1, step2],
        dependencies=[dep],
        risks=[risk],
    )
    assert len(plan.steps) == 2
    assert plan.dependencies[0].source_step_id == "step_1"
    assert plan.risks[0].severity == RiskLevel.MEDIUM
