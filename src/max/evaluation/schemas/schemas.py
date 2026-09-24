"""Pydantic schemas for Module 32 — Evaluation System REST API."""

from typing import Any

from pydantic import BaseModel, Field

from max.evaluation.domain.enums import (
    EvaluationDimension,
    EvaluationType,
    EvaluatorType,
    TargetType,
)


class CaseCreateRequest(BaseModel):
    """Payload to create an evaluation case."""

    name: str = Field(default="Evaluation Case")
    description: str = Field(default="")
    evaluation_type: EvaluationType = Field(default=EvaluationType.QUALITY)
    target_type: TargetType = Field(default=TargetType.AI_RUNTIME)
    input_prompt: str = Field(description="Input prompt or case payload")
    expected_output: str | None = Field(default=None)
    reference_facts: list[str] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)
    expected_security_action: str | None = Field(default=None)
    dimensions: list[EvaluationDimension] = Field(default_factory=lambda: [EvaluationDimension.CORRECTNESS])
    constraints: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class DatasetCreateRequest(BaseModel):
    """Payload to create an evaluation dataset."""

    name: str = Field(description="Dataset name, e.g., max_security_v1")
    description: str = Field(default="")
    cases: list[CaseCreateRequest] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domain: str = Field(default="GENERAL")
    is_golden: bool = Field(default=False)


class DefinitionCreateRequest(BaseModel):
    """Payload to create an evaluation definition."""

    name: str = Field(description="Definition name")
    dataset_id: str = Field(description="Target dataset ID")
    evaluation_type: EvaluationType = Field(default=EvaluationType.QUALITY)
    dataset_version: str = Field(default="1.0.0")
    dimensions: list[EvaluationDimension] = Field(default_factory=lambda: [EvaluationDimension.CORRECTNESS])
    evaluator_types: list[EvaluatorType] = Field(default_factory=lambda: [EvaluatorType.DETERMINISTIC])
    thresholds: dict[str, float] = Field(default_factory=dict)


class RunCreateRequest(BaseModel):
    """Payload to create an evaluation run."""

    dataset_id: str = Field(description="Dataset ID to evaluate")
    definition_id: str | None = Field(default=None)
    target_type: TargetType = Field(default=TargetType.AI_RUNTIME)
    target_id: str = Field(default="system")
    dataset_version: str = Field(default="1.0.0")
    environment_name: str = Field(default="test")


class RunCompareRequest(BaseModel):
    """Payload to compare baseline and candidate evaluation runs."""

    baseline_run_id: str = Field(description="Baseline evaluation run ID")
    candidate_run_id: str = Field(description="Candidate evaluation run ID")
    threshold: float | None = Field(default=None, description="Custom regression threshold")


class StatusResponse(BaseModel):
    """Generic status response DTO."""

    success: bool = Field(default=True)
    message: str = Field(default="Operation completed successfully")
    details: dict[str, Any] = Field(default_factory=dict)
