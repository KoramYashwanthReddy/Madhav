"""Domain models for Module 32 — Evaluation System."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from max.evaluation.domain.enums import (
    CoverageStatus,
    EvaluationDimension,
    EvaluationStatus,
    EvaluationType,
    EvaluatorType,
    FailureCategory,
    RecommendationSeverity,
    ScoreScale,
    TargetType,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _uuid_str() -> str:
    return str(uuid4())


class EvaluationTarget(BaseModel):
    """Abstraction specifying the subject being evaluated."""

    target_type: TargetType = Field(default=TargetType.AI_RUNTIME)
    target_id: str = Field(default="system")
    version: str = Field(default="1.0.0")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationEnvironment(BaseModel):
    """Execution environment details for evaluation reproducibility."""

    environment_name: str = Field(default="test")
    model_identifier: str = Field(default="default_model")
    model_version: str = Field(default="1.0.0")
    runtime_version: str = Field(default="1.0.0")
    application_version: str = Field(default="1.0.0")
    configuration_version: str = Field(default="1.0.0")
    evaluator_version: str = Field(default="1.0.0")
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    random_seed: int | None = Field(default=None)


class EvaluationScore(BaseModel):
    """Normalized score for an evaluation dimension or metric."""

    value: float | str | bool = Field(description="Numeric score, boolean pass/fail, or categorical value")
    scale: ScoreScale = Field(default=ScoreScale.ZERO_TO_ONE)
    metric_name: str = Field(description="Name of metric, e.g. accuracy, faithfulness_score")
    dimension: EvaluationDimension = Field(default=EvaluationDimension.CORRECTNESS)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evaluator_name: str = Field(default="DeterministicEvaluator")
    evaluator_type: EvaluatorType = Field(default=EvaluatorType.DETERMINISTIC)
    reasoning_summary: str | None = Field(default=None, description="Concise non-CoT evaluation rationale")
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationEvidence(BaseModel):
    """Traceable evidence supporting an evaluation score or finding."""

    evidence_id: str = Field(default_factory=_uuid_str)
    case_id: str | None = Field(default=None)
    evidence_type: str = Field(default="OBSERVED_OUTPUT")
    description: str = Field(description="Human readable evidence summary")
    input_reference: str | None = Field(default=None)
    expected_output_reference: str | None = Field(default=None)
    actual_output_reference: str | None = Field(default=None)
    artifact_references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationMetric(BaseModel):
    """Metric definition and aggregated result."""

    metric_id: str = Field(default_factory=_uuid_str)
    name: str = Field(description="Metric identifier, e.g., task_completion_rate")
    dimension: EvaluationDimension = Field(default=EvaluationDimension.TASK_COMPLETION)
    scale: ScoreScale = Field(default=ScoreScale.ZERO_TO_ONE)
    value: float = Field(default=0.0)
    sample_count: int = Field(default=0)
    min_value: float | None = Field(default=None)
    max_value: float | None = Field(default=None)
    p95_value: float | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationCase(BaseModel):
    """Test scenario representing one evaluation case."""

    case_id: str = Field(default_factory=_uuid_str)
    name: str = Field(default="Evaluation Case")
    description: str = Field(default="")
    evaluation_type: EvaluationType = Field(default=EvaluationType.QUALITY)
    target_type: TargetType = Field(default=TargetType.AI_RUNTIME)
    input_prompt: str = Field(description="User prompt or input payload")
    expected_output: str | None = Field(default=None)
    reference_facts: list[str] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)
    expected_tool_args: dict[str, Any] | None = Field(default=None)
    expected_security_action: str | None = Field(default=None)
    expected_status: str | None = Field(default=None)
    dimensions: list[EvaluationDimension] = Field(default_factory=lambda: [EvaluationDimension.CORRECTNESS])
    constraints: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationDatasetVersion(BaseModel):
    """Immutable version tag for an evaluation dataset."""

    version_id: str = Field(default_factory=_uuid_str)
    dataset_id: str
    version_tag: str = Field(default="v1.0.0")
    case_ids: list[str] = Field(default_factory=list)
    case_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utc_now)


class EvaluationDataset(BaseModel):
    """Collection of evaluation test cases."""

    dataset_id: str = Field(default_factory=_uuid_str)
    name: str = Field(description="Dataset name, e.g., max_security_v1")
    description: str = Field(default="")
    version: str = Field(default="1.0.0")
    owner_id: str = Field(default="default_owner")
    cases: list[EvaluationCase] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domain: str = Field(default="GENERAL")
    source: str = Field(default="INTERNAL")
    is_golden: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class EvaluationDefinition(BaseModel):
    """Formal specification of an evaluation configuration."""

    definition_id: str = Field(default_factory=_uuid_str)
    name: str = Field(description="Evaluation suite name")
    description: str = Field(default="")
    evaluation_type: EvaluationType = Field(default=EvaluationType.QUALITY)
    dataset_id: str = Field(description="Target dataset ID")
    dataset_version: str = Field(default="1.0.0")
    dimensions: list[EvaluationDimension] = Field(default_factory=list)
    evaluator_types: list[EvaluatorType] = Field(default_factory=lambda: [EvaluatorType.DETERMINISTIC])
    thresholds: dict[str, float] = Field(default_factory=dict)
    version: str = Field(default="1.0.0")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)


class EvaluationFailure(BaseModel):
    """Classification of an evaluation case failure."""

    failure_id: str = Field(default_factory=_uuid_str)
    case_id: str
    category: FailureCategory = Field(default=FailureCategory.UNKNOWN_FAILURE)
    message: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationResult(BaseModel):
    """Outcome of evaluating one case in a run."""

    result_id: str = Field(default_factory=_uuid_str)
    run_id: str
    case_id: str
    target: EvaluationTarget
    status: EvaluationStatus = Field(default=EvaluationStatus.COMPLETED)
    passed: bool = Field(default=True)
    scores: list[EvaluationScore] = Field(default_factory=list)
    evidence: list[EvaluationEvidence] = Field(default_factory=list)
    failures: list[EvaluationFailure] = Field(default_factory=list)
    actual_output: str | None = Field(default=None)
    latency_ms: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)


class EvaluationExecution(BaseModel):
    """Execution step tracking evaluator invocation."""

    execution_id: str = Field(default_factory=_uuid_str)
    run_id: str
    case_id: str
    evaluator_name: str
    evaluator_type: EvaluatorType
    status: EvaluationStatus = Field(default=EvaluationStatus.COMPLETED)
    error_message: str | None = Field(default=None)
    duration_ms: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationRun(BaseModel):
    """Execution instance of an evaluation definition or dataset."""

    run_id: str = Field(default_factory=_uuid_str)
    definition_id: str | None = Field(default=None)
    dataset_id: str
    dataset_version: str = Field(default="1.0.0")
    target: EvaluationTarget = Field(default_factory=EvaluationTarget)
    environment: EvaluationEnvironment = Field(default_factory=EvaluationEnvironment)
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING)
    start_time: datetime = Field(default_factory=_utc_now)
    end_time: datetime | None = Field(default=None)
    case_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    overall_pass_rate: float = Field(default=0.0)
    metrics: list[EvaluationMetric] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegressionFinding(BaseModel):
    """Detected regression comparing candidate run against baseline run."""

    finding_id: str = Field(default_factory=_uuid_str)
    candidate_run_id: str
    baseline_run_id: str
    dimension: EvaluationDimension
    metric_name: str
    baseline_score: float
    candidate_score: float
    delta: float
    threshold_exceeded: bool = Field(default=True)
    severity: RecommendationSeverity = Field(default=RecommendationSeverity.HIGH)
    description: str = Field(default="")
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationComparison(BaseModel):
    """Comparative analysis between two evaluation runs."""

    comparison_id: str = Field(default_factory=_uuid_str)
    baseline_run_id: str
    candidate_run_id: str
    baseline_pass_rate: float
    candidate_pass_rate: float
    pass_rate_delta: float
    regressions: list[RegressionFinding] = Field(default_factory=list)
    improvements: list[dict[str, Any]] = Field(default_factory=list)
    unchanged_dimensions: list[str] = Field(default_factory=list)
    summary: str = Field(default="")
    created_at: datetime = Field(default_factory=_utc_now)


class EvaluationRecommendation(BaseModel):
    """Informational recommendation produced by evaluation analysis."""

    recommendation_id: str = Field(default_factory=_uuid_str)
    run_id: str
    category: str = Field(default="QUALITY")
    severity: RecommendationSeverity = Field(default=RecommendationSeverity.MEDIUM)
    title: str
    description: str
    suggested_action: str
    timestamp: datetime = Field(default_factory=_utc_now)


class EvaluationCoverage(BaseModel):
    """Coverage metric for a MAX subsystem."""

    subsystem: str
    status: CoverageStatus = Field(default=CoverageStatus.NOT_COVERED)
    total_cases: int = Field(default=0)
    evaluated_cases: int = Field(default=0)
    coverage_percentage: float = Field(default=0.0)


class EvaluationReport(BaseModel):
    """Structured evaluation report detailing run results, metrics, and findings."""

    report_id: str = Field(default_factory=_uuid_str)
    run_id: str
    target: EvaluationTarget
    environment: EvaluationEnvironment
    dataset_name: str
    summary_text: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_pass_rate: float
    metrics: list[EvaluationMetric] = Field(default_factory=list)
    failures: list[EvaluationFailure] = Field(default_factory=list)
    regressions: list[RegressionFinding] = Field(default_factory=list)
    recommendations: list[EvaluationRecommendation] = Field(default_factory=list)
    coverage: list[EvaluationCoverage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)


class EvaluationSummary(BaseModel):
    """High-level system evaluation summary across runs."""

    total_runs: int = Field(default=0)
    total_datasets: int = Field(default=0)
    total_cases_evaluated: int = Field(default=0)
    average_pass_rate: float = Field(default=0.0)
    active_regressions: int = Field(default=0)
    health_status: str = Field(default="HEALTHY")


class EvaluationHealthStatus(BaseModel):
    """Health check status for Module 32 subsystem components."""

    enabled: bool = Field(default=True)
    evaluation_engine_status: str = Field(default="OPERATIONAL")
    registry_status: str = Field(default="OPERATIONAL")
    repository_status: str = Field(default="OPERATIONAL")
    provider_status: str = Field(default="OPERATIONAL")
    dataset_count: int = Field(default=0)
    run_count: int = Field(default=0)
