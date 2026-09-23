"""API Response schemas for Reasoning & Planning Engine."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from max.reasoning.domain.enums import (
    CompletenessStatus,
    ComplexityLevel,
    ConfidenceLevel,
    ConstraintClassification,
    PlanStatus,
    PlanStepStatus,
    ReasoningStatus,
    RiskLevel,
)


class ConstraintResponse(BaseModel):
    """Constraint in response."""

    id: str
    type: str
    description: str
    priority: int
    classification: ConstraintClassification


class ObservationResponse(BaseModel):
    """Observation item."""

    id: str
    description: str
    source_type: str
    source_id: str
    timestamp: datetime


class AssumptionResponse(BaseModel):
    """Assumption item."""

    id: str
    description: str
    confidence: ConfidenceLevel
    source: str | None = None
    status: str


class MissingInformationResponse(BaseModel):
    """Missing info item."""

    id: str
    description: str
    importance: ConfidenceLevel
    is_blocking: bool


class ConclusionResponse(BaseModel):
    """Conclusions payload."""

    summary: str
    key_findings: list[str]
    recommendations: list[str]
    confidence: ConfidenceLevel


class ReasoningResultResponse(BaseModel):
    """Reasoning execution result payload."""

    request_id: str
    status: ReasoningStatus
    objective_summary: str
    observations: list[ObservationResponse]
    assumptions: list[AssumptionResponse]
    constraints: list[ConstraintResponse]
    missing_information: list[MissingInformationResponse]
    conclusions: ConclusionResponse
    plan: dict[str, Any] | None = None
    risks: list[dict[str, Any]] = []
    confidence: ConfidenceLevel
    explanation: str
    metadata: dict[str, Any]
    created_at: datetime


class PlanStepResponse(BaseModel):
    """Step in plan response."""

    step_id: str
    sequence: int
    title: str
    description: str
    objective: str | None = None
    prerequisites: list[str]
    dependencies: list[str]
    expected_output: str | None = None
    estimated_complexity: ComplexityLevel
    risk_level: RiskLevel
    status: PlanStepStatus


class PlanDependencyResponse(BaseModel):
    """Dependency link in response."""

    source_step_id: str
    target_step_id: str
    dependency_type: str


class PlanRiskResponse(BaseModel):
    """Risk item in response."""

    id: str
    description: str
    severity: RiskLevel
    likelihood: RiskLevel
    affected_step_id: str | None = None
    mitigation: str | None = None


class PlanResponse(BaseModel):
    """Full Plan response model."""

    plan_id: str
    owner_id: str
    title: str
    description: str
    version: int
    status: PlanStatus
    steps: list[PlanStepResponse]
    dependencies: list[PlanDependencyResponse]
    risks: list[PlanRiskResponse]
    constraints: list[ConstraintResponse]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PlanListResponse(BaseModel):
    """Paginated list of plans."""

    plans: list[PlanResponse]
    total: int
    skip: int
    limit: int


class PlanValidationResponse(BaseModel):
    """Plan validation response."""

    is_valid: bool
    status: CompletenessStatus
    errors: list[str]
    warnings: list[str]
    has_circular_dependencies: bool


class PlanVersionResponse(BaseModel):
    """Plan version snapshot response."""

    version_id: str
    plan_id: str
    version_number: int
    created_at: datetime
    reason_for_change: str
    previous_version_id: str | None = None
    snapshot: dict[str, Any]


class PlanDiffResponse(BaseModel):
    """Diff comparison response."""

    added_steps: list[str]
    removed_steps: list[str]
    changed_steps: list[str]
    changed_dependencies: list[str]
    changed_constraints: list[str]
    changed_risks: list[str]


class ReasoningSummaryResponse(BaseModel):
    """Summary diagnostic endpoint response."""

    reasoning_enabled: bool
    provider_info: dict[str, Any]
