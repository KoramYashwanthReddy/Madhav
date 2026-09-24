"""Domain models for Module 31 — Learning & Personalization Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from max.personalization.domain.enums import (
    HypothesisStatus,
    LearningMode,
    LearningSignalSource,
    PersonalizationEventType,
    PreferenceScope,
    PreferenceSource,
    PreferenceStatus,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _uuid_str() -> str:
    return str(uuid4())


class Preference(BaseModel):
    """Core user preference entity (explicit or inferred)."""

    preference_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    category: str = Field(default="COMMUNICATION")
    key: str = Field(description="Preference key, e.g., detail_level")
    value: Any = Field(description="Preference value")
    value_type: str = Field(default="str")
    source: PreferenceSource = Field(default=PreferenceSource.EXPLICIT_USER)
    status: PreferenceStatus = Field(default=PreferenceStatus.ACTIVE)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    strength: float = Field(default=1.0, ge=0.0, le=1.0)
    scope: PreferenceScope = Field(default=PreferenceScope.GLOBAL)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    expires_at: datetime | None = Field(default=None)
    effective_from: datetime | None = Field(default=None)
    effective_until: datetime | None = Field(default=None)
    time_window: dict[str, Any] | None = Field(default=None)
    context_conditions: dict[str, Any] | None = Field(default=None)
    version: int = Field(default=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreferenceEvidence(BaseModel):
    """Traceable evidence supporting or contradicting a preference/hypothesis."""

    evidence_id: str = Field(default_factory=_uuid_str)
    preference_id: str | None = Field(default=None)
    hypothesis_id: str | None = Field(default=None)
    source_type: PreferenceSource = Field(default=PreferenceSource.OBSERVED_BEHAVIOR)
    source_reference: str = Field(default="", description="Reference ID or payload snippet")
    observation: str = Field(description="Human-readable observation description")
    weight: float = Field(default=1.0, ge=0.0, le=5.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    is_contradictory: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningSignal(BaseModel):
    """Raw, normalized incoming signal from system interactions."""

    signal_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    source: LearningSignalSource = Field(default=LearningSignalSource.CONVERSATION)
    signal_type: str = Field(description="Event type, e.g., notification_dismissed, answer_expanded")
    observed_at: datetime = Field(default_factory=_utc_now)
    payload_reference: dict[str, Any] = Field(
        default_factory=dict, description="Metadata/references for untrusted payload data"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningObservation(BaseModel):
    """Extracted behavioral observation derived from one or more signals."""

    observation_id: str = Field(default_factory=_uuid_str)
    signal_id: str = Field(description="Source signal ID")
    pattern_type: str = Field(description="Detected pattern type")
    features: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=_utc_now)


class PreferenceHypothesis(BaseModel):
    """Inferred preference candidate evaluated before promotion to active preference."""

    hypothesis_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    category: str = Field(default="COMMUNICATION")
    key: str = Field(description="Target preference key")
    proposed_value: Any = Field(description="Inferred value proposal")
    value_type: str = Field(default="str")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_count: int = Field(default=1, ge=0)
    supporting_evidence: list[str] = Field(default_factory=list, description="List of evidence_ids")
    contradicting_evidence: list[str] = Field(default_factory=list, description="List of evidence_ids")
    status: HypothesisStatus = Field(default=HypothesisStatus.NEW)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommunicationProfile(BaseModel):
    """Structured communication preferences."""

    detail_level: str = Field(default="normal", description="concise, normal, detailed, exhaustive")
    technical_depth: str = Field(default="balanced", description="low, balanced, high, expert")
    response_length: str = Field(default="medium", description="short, medium, long")
    tone: str = Field(default="professional", description="casual, professional, formal")
    format: str = Field(default="markdown")
    examples: bool = Field(default=True)
    code_explanation_level: str = Field(default="normal", description="brief, normal, detailed")
    summary_preference: bool = Field(default=True)
    step_by_step_preference: bool = Field(default=False)
    table_preference: bool = Field(default=False)
    bullet_preference: bool = Field(default=True)


class NotificationProfile(BaseModel):
    """Structured notification preferences."""

    preferred_channels: list[str] = Field(default_factory=lambda: ["in_app"])
    notification_frequency: str = Field(default="normal", description="immediate, digest_hourly, digest_daily, quiet")
    quiet_periods: list[dict[str, Any]] = Field(default_factory=list)
    category_preferences: dict[str, str] = Field(default_factory=dict)
    priority_threshold: str = Field(default="LOW")
    digest_preference: bool = Field(default=False)
    interruption_tolerance: str = Field(default="MEDIUM")


class ProactivityProfile(BaseModel):
    """Structured proactive intelligence behavioral settings."""

    proactive_mode: str = Field(default="NORMAL")
    interruption_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    candidate_relevance_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    preferred_proactive_categories: list[str] = Field(default_factory=list)
    cooldowns: dict[str, float] = Field(default_factory=dict)
    digest_behavior: str = Field(default="OFF")


class AutonomyProfile(BaseModel):
    """Structured autonomy and confirmation preferences (UX preferences ONLY, not permissions)."""

    preferred_autonomy_level: int = Field(default=1, ge=0, le=5)
    approval_preference: str = Field(default="CONFIRM_SENSITIVE")
    confirmation_frequency: str = Field(default="NORMAL")
    trusted_low_risk_actions: list[str] = Field(default_factory=list)
    manual_approval_categories: list[str] = Field(default_factory=list)


class WorkflowProfile(BaseModel):
    """Structured workflow pattern preferences."""

    preferred_patterns: dict[str, str] = Field(
        default_factory=dict, description="e.g. task_execution -> PLAN_REVIEW_EXECUTE"
    )
    approval_steps: list[str] = Field(default_factory=list)
    draft_preview_preference: bool = Field(default=True)


class PersonalizationProfile(BaseModel):
    """Aggregated behavioral personalization profile for a user."""

    profile_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    version: int = Field(default=1)
    preferences: dict[str, Any] = Field(default_factory=dict)
    communication_profile: CommunicationProfile = Field(default_factory=CommunicationProfile)
    notification_profile: NotificationProfile = Field(default_factory=NotificationProfile)
    proactivity_profile: ProactivityProfile = Field(default_factory=ProactivityProfile)
    autonomy_profile: AutonomyProfile = Field(default_factory=AutonomyProfile)
    workflow_profile: WorkflowProfile = Field(default_factory=WorkflowProfile)
    tool_preferences: dict[str, Any] = Field(default_factory=dict)
    voice_preferences: dict[str, Any] = Field(default_factory=dict)
    privacy_preferences: dict[str, Any] = Field(
        default_factory=lambda: {
            "disabled_categories": [],
            "learning_mode": "ADAPTIVE",
            "allow_sensitive_inference": False,
        }
    )
    updated_at: datetime = Field(default_factory=_utc_now)


class ResolvedPreference(BaseModel):
    """Result of deterministic preference resolution for a given key and context."""

    category: str
    key: str
    value: Any
    source: PreferenceSource
    confidence: float
    scope: PreferenceScope
    reason: str
    policy_version: str = Field(default="1.0")


class PersonalizationFeedback(BaseModel):
    """User feedback entity explicitly rating or correcting personalization."""

    feedback_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    preference_id: str | None = Field(default=None)
    hypothesis_id: str | None = Field(default=None)
    feedback_type: str = Field(description="YES, NO, NOT_NOW, DONT_ASK_AGAIN, TOO_SHORT, TOO_LONG, INCORRECT, etc.")
    comments: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)


class PersonalizationHistoryEntry(BaseModel):
    """Audit log entry tracking personalization system decisions and updates."""

    entry_id: str = Field(default_factory=_uuid_str)
    owner_id: str = Field(default="default_owner")
    event_type: PersonalizationEventType
    target_id: str = Field(description="ID of affected preference, hypothesis, or signal")
    changes: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="")
    timestamp: datetime = Field(default_factory=_utc_now)


class PersonalizationSimulationResult(BaseModel):
    """Dry-run outcome evaluating a signal without mutating system state."""

    signal: LearningSignal
    observation: LearningObservation | None = Field(default=None)
    hypothesis: PreferenceHypothesis | None = Field(default=None)
    confidence: float = Field(default=0.0)
    potential_preference: Preference | None = Field(default=None)
    resolution: ResolvedPreference | None = Field(default=None)
    reason: str = Field(default="")


class PersonalizationSettingsState(BaseModel):
    """Current operational state and controls for Module 31."""

    learning_enabled: bool = Field(default=True)
    personalization_enabled: bool = Field(default=True)
    mode: LearningMode = Field(default=LearningMode.ADAPTIVE)
    min_confidence: float = Field(default=0.7)
    min_evidence: int = Field(default=3)
    disabled_categories: list[str] = Field(default_factory=list)
    require_confirmation: bool = Field(default=False)
