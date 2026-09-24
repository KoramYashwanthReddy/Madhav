"""FastAPI REST router for Module 31 — Learning & Personalization Engine."""

import logging

from fastapi import APIRouter, HTTPException, Query, status

from max.personalization.container import PersonalizationContainer
from max.personalization.domain.enums import LearningSignalSource
from max.personalization.domain.exceptions import PersonalizationError
from max.personalization.domain.models import (
    LearningSignal,
    PersonalizationFeedback,
    PersonalizationHistoryEntry,
    PersonalizationProfile,
    PersonalizationSettingsState,
    PersonalizationSimulationResult,
    Preference,
    PreferenceEvidence,
    PreferenceHypothesis,
)
from max.personalization.schemas.schemas import (
    FeedbackCreateRequest,
    PreferenceCorrectRequest,
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    ResetCategoryRequest,
    SettingsUpdateRequest,
    SignalIngestRequest,
    StatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalization", tags=["personalization"])


def _container() -> PersonalizationContainer:
    return PersonalizationContainer.get_instance()


@router.get("/profile", response_model=PersonalizationProfile)
async def get_profile(owner_id: str = "default_owner") -> PersonalizationProfile:
    """Retrieve active user personalization profile."""
    cnt = _container()
    return await cnt.service.profile_service.get_or_create_profile(owner_id)


@router.get("/preferences", response_model=list[Preference])
async def list_preferences(
    owner_id: str = "default_owner",
    category: str | None = Query(default=None),
    key: str | None = Query(default=None),
    active_only: bool = Query(default=True),
) -> list[Preference]:
    """List stored user preferences."""
    cnt = _container()
    return await cnt.preference_repo.list_by_owner(
        owner_id=owner_id, category=category, key=key, active_only=active_only
    )


@router.get("/preferences/{preference_id}", response_model=Preference)
async def get_preference(preference_id: str, owner_id: str = "default_owner") -> Preference:
    """Get preference by ID."""
    cnt = _container()
    pref = await cnt.preference_repo.get_by_id(preference_id)
    if pref is None or pref.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Preference not found.")
    return pref


@router.post("/preferences", response_model=Preference, status_code=status.HTTP_201_CREATED)
async def create_preference(
    payload: PreferenceCreateRequest, owner_id: str = "default_owner"
) -> Preference:
    """Create explicit user preference."""
    cnt = _container()
    try:
        return await cnt.service.create_preference(
            owner_id=owner_id,
            category=payload.category,
            key=payload.key,
            value=payload.value,
            source=payload.source,
            scope=payload.scope,
            metadata=payload.metadata,
        )
    except PersonalizationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.put("/preferences/{preference_id}", response_model=Preference)
async def update_preference(
    preference_id: str, payload: PreferenceUpdateRequest, owner_id: str = "default_owner"
) -> Preference:
    """Update existing user preference."""
    cnt = _container()
    try:
        return await cnt.service.update_preference(
            preference_id=preference_id, value=payload.value, owner_id=owner_id
        )
    except PersonalizationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.delete("/preferences/{preference_id}", response_model=StatusResponse)
async def delete_preference(preference_id: str, owner_id: str = "default_owner") -> StatusResponse:
    """Delete preference by ID."""
    cnt = _container()
    try:
        success = await cnt.service.delete_preference(preference_id, owner_id=owner_id)
        return StatusResponse(success=success, message="Preference deleted cleanly.")
    except PersonalizationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/preferences/{preference_id}/confirm", response_model=Preference)
async def confirm_preference(
    preference_id: str, owner_id: str = "default_owner"
) -> Preference:
    """Confirm a pending/inferred preference or hypothesis."""
    cnt = _container()
    try:
        return await cnt.service.confirm_preference(preference_id, owner_id=owner_id)
    except PersonalizationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/preferences/{preference_id}/reject", response_model=StatusResponse)
async def reject_preference(
    preference_id: str, owner_id: str = "default_owner"
) -> StatusResponse:
    """Reject a pending/inferred preference or hypothesis."""
    cnt = _container()
    try:
        success = await cnt.service.reject_preference(preference_id, owner_id=owner_id)
        return StatusResponse(success=success, message="Preference rejected.")
    except PersonalizationError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc


@router.post("/preferences/{preference_id}/correct", response_model=Preference)
async def correct_preference(
    preference_id: str, payload: PreferenceCorrectRequest, owner_id: str = "default_owner"
) -> Preference:
    """Explicitly correct a preference value."""
    cnt = _container()
    try:
        return await cnt.service.correct_preference(
            preference_id=preference_id,
            correct_value=payload.correct_value,
            owner_id=owner_id,
            comments=payload.comments,
        )
    except PersonalizationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@router.get("/preferences/{preference_id}/evidence", response_model=list[PreferenceEvidence])
async def get_preference_evidence(
    preference_id: str, owner_id: str = "default_owner"
) -> list[PreferenceEvidence]:
    """Retrieve supporting and contradicting evidence for a preference."""
    cnt = _container()
    return await cnt.evidence_repo.list_by_preference(preference_id)


@router.get("/hypotheses", response_model=list[PreferenceHypothesis])
async def list_hypotheses(
    owner_id: str = "default_owner", category: str | None = Query(default=None)
) -> list[PreferenceHypothesis]:
    """List active preference hypotheses."""
    cnt = _container()
    return await cnt.hypothesis_repo.list_by_owner(owner_id=owner_id, category=category)


@router.get("/learning-signals", response_model=list[LearningSignal])
async def list_learning_signals(
    owner_id: str = "default_owner", limit: int = Query(default=100, ge=1, le=1000)
) -> list[LearningSignal]:
    """List logged learning signals."""
    cnt = _container()
    return await cnt.signal_repo.list_by_owner(owner_id=owner_id, limit=limit)


@router.post("/feedback", response_model=PersonalizationFeedback, status_code=status.HTTP_201_CREATED)
async def post_feedback(
    payload: FeedbackCreateRequest, owner_id: str = "default_owner"
) -> PersonalizationFeedback:
    """Post explicit personalization feedback."""
    cnt = _container()
    feedback = PersonalizationFeedback(
        owner_id=owner_id,
        preference_id=payload.preference_id,
        hypothesis_id=payload.hypothesis_id,
        feedback_type=payload.feedback_type,
        comments=payload.comments,
    )
    return await cnt.feedback_repo.save(feedback)


@router.get("/settings", response_model=PersonalizationSettingsState)
async def get_settings_state() -> PersonalizationSettingsState:
    """Retrieve current personalization & learning configuration state."""
    cnt = _container()
    return cnt.service.get_settings_state()


@router.put("/settings", response_model=PersonalizationSettingsState)
async def update_settings(
    payload: SettingsUpdateRequest, owner_id: str = "default_owner"
) -> PersonalizationSettingsState:
    """Update personalization & learning configuration settings."""
    cnt = _container()
    return await cnt.service.update_settings_state(
        learning_enabled=payload.learning_enabled,
        personalization_enabled=payload.personalization_enabled,
        mode=payload.mode,
        disabled_categories=payload.disabled_categories,
        owner_id=owner_id,
    )


@router.post("/pause-learning", response_model=PersonalizationSettingsState)
async def pause_learning(owner_id: str = "default_owner") -> PersonalizationSettingsState:
    """Pause automated behavioral learning."""
    cnt = _container()
    return await cnt.service.update_settings_state(learning_enabled=False, owner_id=owner_id)


@router.post("/resume-learning", response_model=PersonalizationSettingsState)
async def resume_learning(owner_id: str = "default_owner") -> PersonalizationSettingsState:
    """Resume automated behavioral learning."""
    cnt = _container()
    return await cnt.service.update_settings_state(learning_enabled=True, owner_id=owner_id)


@router.post("/reset-inferred", response_model=StatusResponse)
async def reset_inferred_preferences(owner_id: str = "default_owner") -> StatusResponse:
    """Reset all inferred preferences while retaining explicit user preferences."""
    cnt = _container()
    count = await cnt.service.reset_inferred_preferences(owner_id=owner_id)
    return StatusResponse(
        success=True,
        message=f"Reset {count} inferred preferences.",
        details={"deleted_count": count},
    )


@router.post("/reset-category", response_model=StatusResponse)
async def reset_category(
    payload: ResetCategoryRequest, owner_id: str = "default_owner"
) -> StatusResponse:
    """Reset all preferences in a specific category."""
    cnt = _container()
    count = await cnt.service.reset_category(category=payload.category, owner_id=owner_id)
    return StatusResponse(
        success=True,
        message=f"Reset {count} preferences in category '{payload.category}'.",
        details={"deleted_count": count, "category": payload.category},
    )


@router.post("/simulate", response_model=PersonalizationSimulationResult)
async def simulate_signal(
    payload: SignalIngestRequest, owner_id: str = "default_owner"
) -> PersonalizationSimulationResult:
    """Dry-run simulation evaluating a learning signal without modifying state."""
    cnt = _container()
    signal = LearningSignal(
        owner_id=owner_id,
        source=LearningSignalSource(payload.source.upper()),
        signal_type=payload.signal_type,
        payload_reference=payload.payload_reference,
        metadata=payload.metadata,
    )
    return await cnt.service.simulate(signal)


@router.get("/history", response_model=list[PersonalizationHistoryEntry])
async def list_history(
    owner_id: str = "default_owner", limit: int = Query(default=100, ge=1, le=1000)
) -> list[PersonalizationHistoryEntry]:
    """Retrieve audit history log entries for personalization."""
    cnt = _container()
    return await cnt.history_repo.list_by_owner(owner_id=owner_id, limit=limit)
