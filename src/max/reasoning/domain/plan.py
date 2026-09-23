"""Plan Domain Models for Module 11 Reasoning & Planning Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from max.reasoning.domain.enums import (
    CompletenessStatus,
    ComplexityLevel,
    PlanStatus,
    PlanStepStatus,
    RiskLevel,
)
from max.reasoning.domain.exceptions import PlanValidationError
from max.reasoning.domain.reasoning import ReasoningConstraint


class PlanStep(BaseModel):
    """Domain model representing a single step within a Plan."""

    step_id: str = Field(
        default_factory=lambda: f"step_{uuid4().hex[:8]}", description="Unique step identifier"
    )
    sequence: int = Field(description="1-based sequence order index")
    title: str = Field(description="Step title")
    description: str = Field(description="Detailed step description")
    objective: str | None = Field(default=None, description="Specific sub-objective of step")
    prerequisites: list[str] = Field(
        default_factory=list, description="Prerequisite condition descriptions or IDs"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Explicit step_ids that MUST precede this step"
    )
    expected_output: str | None = Field(
        default=None, description="Expected outcome string descriptor"
    )
    estimated_complexity: ComplexityLevel = Field(
        default=ComplexityLevel.MEDIUM, description="Estimated complexity level"
    )
    risk_level: RiskLevel = Field(
        default=RiskLevel.LOW, description="Estimated risk classification"
    )
    status: PlanStepStatus = Field(
        default=PlanStepStatus.PENDING, description="Current step status"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata"
    )

    @model_validator(mode="after")
    def validate_step(self) -> "PlanStep":
        """Validate step properties."""
        if not self.title or not self.title.strip():
            raise PlanValidationError("PlanStep title cannot be empty.")
        if self.sequence <= 0:
            raise PlanValidationError("PlanStep sequence must be a positive integer.")
        return self


class PlanDependency(BaseModel):
    """Explicit dependency link between plan steps."""

    source_step_id: str = Field(description="Preceding prerequisite step identifier")
    target_step_id: str = Field(description="Dependent step identifier")
    dependency_type: str = Field(
        default="FINISH_TO_START", description="Dependency relationship type"
    )


class PlanRisk(BaseModel):
    """Identified risk item associated with a plan."""

    id: str = Field(default_factory=lambda: f"risk_{uuid4().hex[:8]}")
    description: str = Field(description="Risk description text")
    severity: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk severity rating")
    likelihood: RiskLevel = Field(default=RiskLevel.MEDIUM, description="Risk likelihood rating")
    affected_step_id: str | None = Field(
        default=None, description="Optional target step identifier affected"
    )
    mitigation: str | None = Field(
        default=None, description="Optional proposed mitigation strategy"
    )


class PlanValidationResult(BaseModel):
    """Structural plan validation inspection result."""

    is_valid: bool = Field(description="Whether plan passes all structural validation rules")
    status: CompletenessStatus = Field(description="Overall plan completeness status")
    errors: list[str] = Field(default_factory=list, description="Validation error messages")
    warnings: list[str] = Field(default_factory=list, description="Validation warning messages")
    has_circular_dependencies: bool = Field(
        default=False, description="Whether circular dependencies were detected"
    )


class PlanVersion(BaseModel):
    """Historical version snapshot of a Plan."""

    version_id: str = Field(
        default_factory=lambda: f"ver_{uuid4().hex[:8]}", description="Version snapshot unique ID"
    )
    plan_id: str = Field(description="Parent Plan identifier")
    version_number: int = Field(description="Sequential 1-based version number")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Snapshot creation timestamp"
    )
    reason_for_change: str = Field(description="Description of reason for plan revision")
    previous_version_id: str | None = Field(
        default=None, description="Parent version ID if applicable"
    )
    snapshot: dict[str, Any] = Field(
        description="Complete serialized plan state snapshot"
    )


class Plan(BaseModel):
    """Domain model representing a structured sequence of intended planning steps."""

    plan_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Plan unique identifier"
    )
    owner_id: str = Field(description="Owner user identifier")
    title: str = Field(description="Plan title")
    description: str = Field(description="Plan scope description")
    version: int = Field(default=1, description="Current plan version number")
    status: PlanStatus = Field(default=PlanStatus.DRAFT, description="Plan lifecycle status")
    steps: list[PlanStep] = Field(default_factory=list, description="Sequence of plan steps")
    dependencies: list[PlanDependency] = Field(
        default_factory=list, description="Explicit step dependencies"
    )
    risks: list[PlanRisk] = Field(default_factory=list, description="Identified plan risks")
    constraints: list[ReasoningConstraint] = Field(
        default_factory=list, description="Planning constraints"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )


    @model_validator(mode="after")
    def validate_plan_basics(self) -> "Plan":
        """Validate plan fields."""
        if not self.owner_id or not self.owner_id.strip():
            raise PlanValidationError("Plan owner_id cannot be empty.")
        if not self.title or not self.title.strip():
            raise PlanValidationError("Plan title cannot be empty.")
        return self


class PlanDiff(BaseModel):
    """Structured comparison result between two plan versions."""

    added_steps: list[str] = Field(default_factory=list, description="Step titles/IDs added")
    removed_steps: list[str] = Field(default_factory=list, description="Step titles/IDs removed")
    changed_steps: list[str] = Field(default_factory=list, description="Step titles/IDs modified")
    changed_dependencies: list[str] = Field(
        default_factory=list, description="Dependencies modified"
    )
    changed_constraints: list[str] = Field(default_factory=list, description="Constraints modified")
    changed_risks: list[str] = Field(default_factory=list, description="Risks modified")
