"""API Request schemas for Reasoning & Planning Engine."""

from typing import Any

from pydantic import BaseModel, Field

from max.reasoning.domain.enums import (
    ComplexityLevel,
    ConstraintClassification,
    PlanStepStatus,
    ReasoningMode,
    RiskLevel,
)


class ConstraintPayload(BaseModel):
    """Constraint payload."""

    type: str = Field(description="Constraint type (e.g. 'time', 'budget')")
    description: str = Field(description="Constraint text")
    priority: int = Field(default=1, description="Priority")
    classification: ConstraintClassification = Field(
        default=ConstraintClassification.HARD, description="HARD or SOFT"
    )


class ObjectivePayload(BaseModel):
    """Objective payload."""

    title: str = Field(description="Objective title")
    description: str = Field(default="", description="Objective description")
    desired_outcome: str = Field(default="", description="Desired outcome")
    success_criteria: list[str] = Field(default_factory=list, description="Criteria")
    priority: int = Field(default=1, description="Priority")
    constraints: list[ConstraintPayload] = Field(default_factory=list)


class CreateReasoningRequestPayload(BaseModel):
    """Payload to create and execute a reasoning request."""

    owner_id: str = Field(description="Owner user ID")
    objective: ObjectivePayload = Field(description="Objective payload")
    mode: ReasoningMode = Field(default=ReasoningMode.PLANNING, description="Reasoning mode")
    constraints: list[ConstraintPayload] = Field(default_factory=list)
    plan_depth: int = Field(default=1, description="Planning depth")
    metadata: dict[str, Any] = Field(default_factory=dict)


class StepPayload(BaseModel):
    """Plan step payload."""

    step_id: str | None = Field(default=None, description="Step ID")
    sequence: int = Field(description="1-based sequence")
    title: str = Field(description="Step title")
    description: str = Field(description="Step description")
    dependencies: list[str] = Field(default_factory=list, description="Preceding step IDs")
    prerequisites: list[str] = Field(default_factory=list)
    estimated_complexity: ComplexityLevel = Field(default=ComplexityLevel.MEDIUM)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING)


class DependencyPayload(BaseModel):
    """Plan dependency payload."""

    source_step_id: str = Field(description="Source step ID")
    target_step_id: str = Field(description="Target step ID")


class RiskPayload(BaseModel):
    """Plan risk payload."""

    description: str = Field(description="Risk description")
    severity: RiskLevel = Field(default=RiskLevel.MEDIUM)
    likelihood: RiskLevel = Field(default=RiskLevel.MEDIUM)
    mitigation: str | None = Field(default=None)


class CreatePlanPayload(BaseModel):
    """Payload to create a plan directly."""

    owner_id: str = Field(description="Owner user ID")
    title: str = Field(description="Plan title")
    description: str = Field(default="", description="Plan description")
    steps: list[StepPayload] = Field(default_factory=list)
    dependencies: list[DependencyPayload] = Field(default_factory=list)
    risks: list[RiskPayload] = Field(default_factory=list)
    constraints: list[ConstraintPayload] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RevisePlanPayload(BaseModel):
    """Payload to revise an existing plan."""

    reason_for_change: str = Field(description="Reason for revision")
    steps: list[StepPayload] | None = Field(default=None)
    dependencies: list[DependencyPayload] | None = Field(default=None)
    risks: list[RiskPayload] | None = Field(default=None)
    constraints: list[ConstraintPayload] | None = Field(default=None)
