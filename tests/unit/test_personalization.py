"""Unit tests for Module 31 — Learning & Personalization Engine."""

from datetime import UTC, datetime, timedelta

import pytest

from max.config.sections import PersonalizationSettings
from max.personalization.domain.enums import (
    HypothesisStatus,
    LearningSignalSource,
    PreferenceSource,
    PreferenceStatus,
)
from max.personalization.domain.exceptions import (
    PermissionEscalationViolationError,
    SensitiveInferenceViolationError,
)
from max.personalization.domain.models import (
    LearningSignal,
    Preference,
)
from max.personalization.repositories.repositories import (
    InMemoryFeedbackRepository,
    InMemoryHypothesisRepository,
    InMemoryLearningSignalRepository,
    InMemoryObservationRepository,
    InMemoryPersonalizationHistoryRepository,
    InMemoryPersonalizationProfileRepository,
    InMemoryPreferenceEvidenceRepository,
    InMemoryPreferenceRepository,
)
from max.personalization.services.personalization_service import PersonalizationService
from max.personalization.services.policy_validator import PolicyValidator


@pytest.fixture
def service() -> PersonalizationService:
    settings = PersonalizationSettings(
        enabled=True,
        learning_enabled=True,
        mode="ADAPTIVE",
        min_confidence=0.7,
        min_evidence=3,
        decay_rate=0.05,
    )
    return PersonalizationService(
        settings=settings,
        preference_repo=InMemoryPreferenceRepository(),
        evidence_repo=InMemoryPreferenceEvidenceRepository(),
        signal_repo=InMemoryLearningSignalRepository(),
        observation_repo=InMemoryObservationRepository(),
        hypothesis_repo=InMemoryHypothesisRepository(),
        profile_repo=InMemoryPersonalizationProfileRepository(),
        feedback_repo=InMemoryFeedbackRepository(),
        history_repo=InMemoryPersonalizationHistoryRepository(),
    )


@pytest.mark.asyncio
async def test_explicit_preference_creation(service: PersonalizationService):
    """Test explicit user preference creation."""
    pref = await service.create_preference(
        owner_id="user1",
        category="COMMUNICATION",
        key="detail_level",
        value="detailed",
        source=PreferenceSource.EXPLICIT_USER,
    )
    assert pref.key == "detail_level"
    assert pref.value == "detailed"
    assert pref.confidence == 1.0
    assert pref.source == PreferenceSource.EXPLICIT_USER

    resolved = await service.resolve_preference(category="COMMUNICATION", key="detail_level", owner_id="user1")
    assert resolved.value == "detailed"
    assert resolved.source == PreferenceSource.EXPLICIT_USER


@pytest.mark.asyncio
async def test_important_explicit_preference_overrides_inferred(service: PersonalizationService):
    """IMPORTANT EXPLICIT PREFERENCE TEST: Explicit user preference remains authoritative despite contradictory noise."""
    # 1. User explicitly states preference
    await service.create_preference(
        owner_id="user1",
        category="COMMUNICATION",
        key="detail_level",
        value="detailed",
        source=PreferenceSource.EXPLICIT_USER,
    )

    # 2. Repeated noisy observations (user sometimes asks for concise answer)
    for _ in range(5):
        sig = LearningSignal(
            owner_id="user1",
            source=LearningSignalSource.CONVERSATION,
            signal_type="answer_shortened",
        )
        await service.ingest_signal(sig)

    # 3. Explicit preference MUST remain authoritative
    resolved = await service.resolve_preference(category="COMMUNICATION", key="detail_level", owner_id="user1")
    assert resolved.value == "detailed"
    assert resolved.source == PreferenceSource.EXPLICIT_USER


@pytest.mark.asyncio
async def test_important_learning_hypothesis_generation(service: PersonalizationService):
    """IMPORTANT LEARNING TEST: Repeated dismissals generate hypothesis without instant explicit promotion."""
    # Repeated dismissals of low priority notifications
    for _ in range(2):
        sig = LearningSignal(
            owner_id="user1",
            source=LearningSignalSource.NOTIFICATION,
            signal_type="notification_dismissed",
            payload_reference={"notification_category": "LOW_PRIORITY"},
        )
        await service.ingest_signal(sig)

    hypotheses = await service.hypothesis_repo.list_by_owner("user1", category="NOTIFICATION")
    assert len(hypotheses) == 1
    assert hypotheses[0].key == "notification_frequency"
    assert hypotheses[0].status in (HypothesisStatus.NEW, HypothesisStatus.STRENGTHENING)

    # Not yet promoted until min_evidence count (3) reached
    prefs = await service.preference_repo.list_by_owner("user1", category="NOTIFICATION")
    assert len(prefs) == 0


@pytest.mark.asyncio
async def test_important_correction_test(service: PersonalizationService):
    """IMPORTANT CORRECTION TEST: Explicit user correction wins over inferred preference."""
    # 1. Inferred preference exists
    inferred_pref = Preference(
        owner_id="user1",
        category="COMMUNICATION",
        key="detail_level",
        value="concise",
        source=PreferenceSource.OBSERVED_BEHAVIOR,
        status=PreferenceStatus.ACTIVE,
        confidence=0.8,
    )
    await service.preference_repo.save(inferred_pref)

    # 2. User explicitly corrects MAX: "I actually want detailed responses."
    corrected = await service.correct_preference(
        preference_id=inferred_pref.preference_id,
        correct_value="detailed",
        owner_id="user1",
        comments="I actually want detailed responses.",
    )

    assert corrected.value == "detailed"
    assert corrected.source == PreferenceSource.USER_CORRECTION
    assert corrected.confidence == 1.0

    resolved = await service.resolve_preference(category="COMMUNICATION", key="detail_level", owner_id="user1")
    assert resolved.value == "detailed"
    assert resolved.source == PreferenceSource.USER_CORRECTION


@pytest.mark.asyncio
async def test_important_security_test(service: PersonalizationService):
    """IMPORTANT SECURITY TEST: Rejects AI hypothesis attempting security permission alteration."""
    policy_validator = PolicyValidator()

    with pytest.raises(PermissionEscalationViolationError):
        policy_validator.validate_hypothesis(
            category="AUTONOMY",
            key="unrestricted_shell_execution",
            proposed_value=True,
            observation="User often approves shell commands",
        )

    with pytest.raises(PermissionEscalationViolationError):
        await service.create_preference(
            owner_id="user1",
            category="AUTONOMY",
            key="bypass_security_checks",
            value=True,
        )


@pytest.mark.asyncio
async def test_important_sensitive_inference_test(service: PersonalizationService):
    """IMPORTANT SENSITIVE INFERENCE TEST: Rejects forbidden sensitive personal inferences."""
    policy_validator = PolicyValidator(allow_sensitive_inference=False)

    with pytest.raises(SensitiveInferenceViolationError):
        policy_validator.validate_hypothesis(
            category="PRIVACY",
            key="user_political_affiliation",
            proposed_value="conservative",
            observation="User reads political articles",
        )

    with pytest.raises(SensitiveInferenceViolationError):
        policy_validator.validate_hypothesis(
            category="PRIVACY",
            key="user_mental_health",
            proposed_value="depressed",
            observation="User asked health questions",
        )


@pytest.mark.asyncio
async def test_important_silence_test(service: PersonalizationService):
    """IMPORTANT SILENCE TEST: One weak observation does not create permanent preference."""
    sig = LearningSignal(
        owner_id="user1",
        source=LearningSignalSource.NOTIFICATION,
        signal_type="notification_dismissed",
    )
    await service.ingest_signal(sig)

    prefs = await service.preference_repo.list_by_owner("user1")
    assert len(prefs) == 0  # No permanent preference created from single weak signal!


@pytest.mark.asyncio
async def test_important_reset_test(service: PersonalizationService):
    """IMPORTANT RESET TEST: Reset inferred preferences removes inferred while preserving explicit."""
    # Create explicit preference
    await service.create_preference(
        owner_id="user1",
        category="COMMUNICATION",
        key="detail_level",
        value="detailed",
        source=PreferenceSource.EXPLICIT_USER,
    )

    # Create inferred preference
    inferred = Preference(
        owner_id="user1",
        category="NOTIFICATION",
        key="notification_frequency",
        value="digest",
        source=PreferenceSource.OBSERVED_BEHAVIOR,
        status=PreferenceStatus.ACTIVE,
    )
    await service.preference_repo.save(inferred)

    # Reset inferred preferences
    reset_count = await service.reset_inferred_preferences(owner_id="user1")
    assert reset_count == 1

    remaining = await service.preference_repo.list_by_owner("user1", active_only=True)
    assert len(remaining) == 1
    assert remaining[0].key == "detail_level"
    assert remaining[0].source == PreferenceSource.EXPLICIT_USER


@pytest.mark.asyncio
async def test_preference_decay(service: PersonalizationService):
    """Test confidence decay over time for inferred preferences."""
    now = datetime.now(UTC)
    old_time = now - timedelta(days=10)

    inferred = Preference(
        owner_id="user1",
        category="COMMUNICATION",
        key="tone",
        value="casual",
        source=PreferenceSource.OBSERVED_BEHAVIOR,
        status=PreferenceStatus.ACTIVE,
        confidence=0.8,
        updated_at=old_time,
    )
    await service.preference_repo.save(inferred)

    decayed_count, expired_count = await service.decay_service.run_decay_cycle(owner_id="user1", current_time=now)
    assert decayed_count == 1

    updated_pref = await service.preference_repo.get_by_id(inferred.preference_id)
    assert updated_pref is not None
    assert updated_pref.confidence < 0.8


@pytest.mark.asyncio
async def test_simulation_dry_run(service: PersonalizationService):
    """Test dry-run simulation does not alter persistent database state."""
    sig = LearningSignal(
        owner_id="user1",
        source=LearningSignalSource.CONVERSATION,
        signal_type="answer_expanded",
    )
    sim_result = await service.simulate(sig)
    assert sim_result.observation is not None
    assert sim_result.confidence > 0.0

    # Verify persistent store remains unchanged
    signals = await service.signal_repo.list_by_owner("user1")
    assert len(signals) == 0


@pytest.mark.asyncio
async def test_pause_and_resume_learning(service: PersonalizationService):
    """Test pausing and resuming learning mode."""
    await service.update_settings_state(learning_enabled=False, owner_id="user1")
    state = service.get_settings_state()
    assert state.learning_enabled is False

    sig = LearningSignal(
        owner_id="user1",
        source=LearningSignalSource.CONVERSATION,
        signal_type="answer_expanded",
    )
    obs, hyp, pref = await service.ingest_signal(sig)
    assert obs is None
    assert hyp is None
    assert pref is None

    await service.update_settings_state(learning_enabled=True, owner_id="user1")
    state = service.get_settings_state()
    assert state.learning_enabled is True
