"""Pydantic request and response schemas for Module 30 REST API."""

from typing import Any

from pydantic import BaseModel, Field

from max.proactive.domain.enums import (
    AutonomyLevel,
    DecisionType,
    FeedbackType,
    ImportanceLevel,
    ProactiveMode,
    RulePriority,
    SignalSource,
    UrgencyLevel,
    UserState,
)
from max.proactive.domain.models import (
    ProactiveCandidate,
    ProactiveDecision,
    ProactiveSignal,
)


class SignalIngestRequest(BaseModel):
    """Payload for submitting a new proactive signal."""

    source: SignalSource
    signal_type: str = Field(examples=["calendar.deadline_approaching"])
    payload_reference: dict[str, Any] = Field(default_factory=dict)
    importance_hint: ImportanceLevel = Field(default=ImportanceLevel.MEDIUM)
    deduplication_key: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SignalResponse(BaseModel):
    """API response model for an ingested signal."""

    signal: ProactiveSignal
    candidates_count: int


class CandidateResponse(BaseModel):
    """API response model for proactive candidates."""

    candidates: list[ProactiveCandidate]
    total: int


class DecisionResponse(BaseModel):
    """API response model for proactive decisions."""

    decisions: list[ProactiveDecision]
    total: int


class RuleCreateRequest(BaseModel):
    """Payload for creating a new proactive rule."""

    name: str
    description: str
    source: SignalSource | None = Field(default=None)
    candidate_type: str | None = Field(default=None)
    min_importance: ImportanceLevel = Field(default=ImportanceLevel.LOW)
    min_urgency: UrgencyLevel = Field(default=UrgencyLevel.LOW)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    min_relevance: float = Field(default=0.5, ge=0.0, le=1.0)
    allowed_user_states: list[UserState] = Field(
        default_factory=lambda: [UserState.AVAILABLE, UserState.FOCUSED]
    )
    decision_type: DecisionType = Field(default=DecisionType.NOTIFY)
    priority: RulePriority = Field(default=RulePriority.DEFAULT)
    cooldown_seconds: float = Field(default=14400.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackCreateRequest(BaseModel):
    """Payload for submitting user feedback."""

    decision_id: str
    feedback_type: FeedbackType
    value: str | float | int | bool = Field(default=True)
    source: str = Field(default="USER_EXPLICIT")
    metadata: dict[str, Any] = Field(default_factory=dict)


class StatusResponse(BaseModel):
    """System health and operational status for Module 30."""

    enabled: bool
    mode: ProactiveMode
    user_state: UserState
    default_autonomy_level: AutonomyLevel
    hourly_notifications_remaining: int
    daily_notifications_remaining: int
    active_rules_count: int
