"""Reasoning Domain Models for Module 11 Reasoning & Planning Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from max.reasoning.domain.enums import (
    ConfidenceLevel,
    ConstraintClassification,
    ReasoningMode,
    ReasoningStatus,
)
from max.reasoning.domain.exceptions import ReasoningRequestValidationError


class ReasoningConstraint(BaseModel):
    """Domain model representing a hard or soft constraint."""

    id: str = Field(default_factory=lambda: f"cst_{uuid4().hex[:8]}")
    type: str = Field(description="Constraint category (e.g. 'time', 'technology', 'budget')")
    description: str = Field(description="Constraint text description")
    priority: int = Field(default=1, description="Constraint priority level")
    classification: ConstraintClassification = Field(
        default=ConstraintClassification.HARD, description="HARD vs SOFT constraint boundary"
    )


class ReasoningObjective(BaseModel):
    """Structured goal or target objective definition."""

    title: str = Field(description="Canonical objective title")
    description: str = Field(description="Detailed objective description")
    desired_outcome: str = Field(description="Explicit desired outcome statement")
    success_criteria: list[str] = Field(
        default_factory=list, description="Measurable success criteria items"
    )
    priority: int = Field(default=1, description="Objective priority ranking")
    deadline: datetime | None = Field(
        default=None, description="Optional explicit deadline timestamp"
    )
    constraints: list[ReasoningConstraint] = Field(
        default_factory=list, description="Objective-specific constraints"
    )


    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is non-empty."""
        if not v or not v.strip():
            raise ValueError("ReasoningObjective title cannot be empty.")
        return v


class ReasoningAssumption(BaseModel):
    """Explicit assumption used during reasoning."""

    id: str = Field(default_factory=lambda: f"asm_{uuid4().hex[:8]}")
    description: str = Field(description="Text description of the assumption")
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Assumed confidence rating"
    )
    source: str | None = Field(default=None, description="Optional origin reference")
    status: str = Field(default="ACTIVE", description="Assumption state indicator")


class ReasoningObservation(BaseModel):
    """Fact or evidence observation extracted from context."""

    id: str = Field(default_factory=lambda: f"obs_{uuid4().hex[:8]}")
    description: str = Field(description="Observation statement text")
    source_type: str = Field(
        description="Source classification ('conversation', 'memory', 'knowledge', 'rag')"
    )

    source_id: str = Field(description="Source reference identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Observation capture timestamp"
    )


class MissingInformation(BaseModel):
    """Identified missing knowledge or unresolved requirement."""

    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:8]}")
    description: str = Field(description="Description of missing information required")
    importance: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Importance level of missing information"
    )
    is_blocking: bool = Field(
        default=False, description="Whether this missing information blocks planning"
    )


class ReasoningConclusion(BaseModel):
    """Structured conclusion and recommendation payload."""

    summary: str = Field(description="Concise cognitive synthesis summary")
    key_findings: list[str] = Field(default_factory=list, description="Extracted key findings")
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable recommended directions"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Overall conclusion confidence rating"
    )


class ReasoningEvidence(BaseModel):
    """Provenance citation linking reasoning conclusions back to evidence sources."""

    source_type: str = Field(description="Source category (e.g. 'memory', 'knowledge', 'rag')")
    source_id: str = Field(description="Source identifier")
    summary: str = Field(description="Evidence excerpt or summary")
    location: str | None = Field(default=None, description="Optional paragraph/section location")


class ReasoningContext(BaseModel):
    """Explicit container for context elements supplied to reasoning."""

    conversation_items: list[dict[str, str | int | float | bool | list[str]]] = Field(
        default_factory=list, description="Conversation context records"
    )
    memory_items: list[dict[str, str | int | float | bool | list[str]]] = Field(
        default_factory=list, description="Memory Engine records"
    )
    knowledge_items: list[dict[str, str | int | float | bool | list[str]]] = Field(
        default_factory=list, description="Personal Knowledge records"
    )
    retrieval_items: list[dict[str, str | int | float | bool | list[str]]] = Field(
        default_factory=list, description="RAG Engine retrieved records"
    )
    constraints: list[ReasoningConstraint] = Field(
        default_factory=list, description="Extracted contextual constraints"
    )
    assumptions: list[ReasoningAssumption] = Field(
        default_factory=list, description="Contextual assumptions"
    )


class ReasoningRequest(BaseModel):
    """Domain model representing a structured reasoning and planning request."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Reasoning request unique identifier"
    )
    owner_id: str = Field(description="Owner user identifier")
    objective: ReasoningObjective = Field(description="Primary objective specification")
    context: ReasoningContext = Field(
        default_factory=ReasoningContext, description="Supplied reasoning context"
    )
    constraints: list[ReasoningConstraint] = Field(
        default_factory=list, description="Top-level request constraints"
    )
    mode: ReasoningMode = Field(
        default=ReasoningMode.PLANNING, description="Requested reasoning cognitive mode"
    )
    plan_depth: int = Field(default=1, description="Depth level of hierarchical planning")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary safe metadata key-value pairs"
    )

    @model_validator(mode="after")
    def validate_request_fields(self) -> "ReasoningRequest":
        """Validate reasoning request attributes."""
        if not self.owner_id or not self.owner_id.strip():
            raise ReasoningRequestValidationError("ReasoningRequest owner_id cannot be empty.")

        if not self.objective.title or not self.objective.title.strip():
            raise ReasoningRequestValidationError("ReasoningObjective title cannot be empty.")

        return self


class ReasoningResult(BaseModel):
    """Domain model representing the machine-readable result of cognitive reasoning."""

    request_id: str = Field(description="Associated reasoning request identifier")
    status: ReasoningStatus = Field(
        default=ReasoningStatus.COMPLETED, description="Execution status"
    )
    objective_summary: str = Field(description="Summary of the evaluated objective")
    observations: list[ReasoningObservation] = Field(
        default_factory=list, description="Extracted contextual observations"
    )
    assumptions: list[ReasoningAssumption] = Field(
        default_factory=list, description="Identified cognitive assumptions"
    )
    constraints: list[ReasoningConstraint] = Field(
        default_factory=list, description="Evaluated hard and soft constraints"
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list, description="Identified missing information items"
    )
    conclusions: ReasoningConclusion = Field(description="Structured conclusions payload")
    plan: dict[str, Any] | None = Field(
        default=None, description="Generated Plan representation dict if mode includes PLANNING"
    )
    risks: list[dict[str, Any]] = Field(
        default_factory=list, description="Identified risk items"
    )
    evidence: list[ReasoningEvidence] = Field(
        default_factory=list, description="Evidence citations linking back to context"
    )
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM, description="Overall reasoning confidence"
    )
    explanation: str = Field(description="Concise user-facing explanation summary")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution diagnostic metadata"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Result creation timestamp"
    )

