"""Central orchestration engine for Module 31 — Learning & Personalization Engine."""

import logging
from datetime import UTC, datetime
from typing import Any

from max.config.sections import PersonalizationSettings
from max.personalization.domain.enums import (
    HypothesisStatus,
    LearningMode,
    PersonalizationEventType,
    PreferenceScope,
    PreferenceSource,
    PreferenceStatus,
)
from max.personalization.domain.exceptions import (
    PreferenceNotFoundError,
)
from max.personalization.domain.models import (
    LearningObservation,
    LearningSignal,
    PersonalizationFeedback,
    PersonalizationHistoryEntry,
    PersonalizationSettingsState,
    PersonalizationSimulationResult,
    Preference,
    PreferenceEvidence,
    PreferenceHypothesis,
    ResolvedPreference,
)
from max.personalization.repositories.interfaces import (
    FeedbackRepository,
    HypothesisRepository,
    LearningSignalRepository,
    ObservationRepository,
    PersonalizationHistoryRepository,
    PersonalizationProfileRepository,
    PreferenceEvidenceRepository,
    PreferenceRepository,
)
from max.personalization.services.confidence_evaluator import ConfidenceEvaluator
from max.personalization.services.decay_service import PreferenceDecayService
from max.personalization.services.hypothesis_engine import HypothesisEngine
from max.personalization.services.inference_provider import (
    DeterministicPersonalizationProvider,
    PersonalizationInferenceProvider,
)
from max.personalization.services.pattern_detector import PatternDetector
from max.personalization.services.policy_validator import PolicyValidator
from max.personalization.services.preference_resolver import PreferenceResolver
from max.personalization.services.profile_service import PersonalizationProfileService

logger = logging.getLogger(__name__)


class PersonalizationService:
    """Core orchestration engine managing personalization, learning, user controls, and audit trails."""

    def __init__(
        self,
        settings: PersonalizationSettings,
        preference_repo: PreferenceRepository,
        evidence_repo: PreferenceEvidenceRepository,
        signal_repo: LearningSignalRepository,
        observation_repo: ObservationRepository,
        hypothesis_repo: HypothesisRepository,
        profile_repo: PersonalizationProfileRepository,
        feedback_repo: FeedbackRepository,
        history_repo: PersonalizationHistoryRepository,
    ) -> None:
        self.settings = settings
        self.preference_repo = preference_repo
        self.evidence_repo = evidence_repo
        self.signal_repo = signal_repo
        self.observation_repo = observation_repo
        self.hypothesis_repo = hypothesis_repo
        self.profile_repo = profile_repo
        self.feedback_repo = feedback_repo
        self.history_repo = history_repo

        # Internal state settings override (supports pause/resume dynamically)
        self._learning_enabled = settings.learning_enabled
        self._personalization_enabled = settings.personalization_enabled
        self._learning_mode = LearningMode(settings.mode.upper())
        self._disabled_categories: set[str] = set()

        # Services initialization
        self.policy_validator = PolicyValidator()
        self.confidence_evaluator = ConfidenceEvaluator(default_decay_rate=settings.decay_rate)
        self.pattern_detector = PatternDetector()
        self.inference_provider: PersonalizationInferenceProvider = (
            DeterministicPersonalizationProvider(self.pattern_detector)
        )
        self.hypothesis_engine = HypothesisEngine(
            hypothesis_repo=self.hypothesis_repo,
            evidence_repo=self.evidence_repo,
            preference_repo=self.preference_repo,
            policy_validator=self.policy_validator,
            confidence_evaluator=self.confidence_evaluator,
            min_confidence=settings.min_confidence,
            min_evidence=settings.min_evidence,
            mode=self._learning_mode,
        )
        self.resolver = PreferenceResolver(preference_repo=self.preference_repo)
        self.profile_service = PersonalizationProfileService(
            profile_repo=self.profile_repo,
            preference_repo=self.preference_repo,
            resolver=self.resolver,
        )
        self.decay_service = PreferenceDecayService(
            preference_repo=self.preference_repo,
            confidence_evaluator=self.confidence_evaluator,
            decay_rate=settings.decay_rate,
        )

    # ------------------------------------------------------------------
    # Settings & Controls
    # ------------------------------------------------------------------

    def get_settings_state(self) -> PersonalizationSettingsState:
        return PersonalizationSettingsState(
            learning_enabled=self._learning_enabled,
            personalization_enabled=self._personalization_enabled,
            mode=self._learning_mode,
            min_confidence=self.settings.min_confidence,
            min_evidence=self.settings.min_evidence,
            disabled_categories=list(self._disabled_categories),
            require_confirmation=self.settings.require_confirmation,
        )

    async def update_settings_state(
        self,
        learning_enabled: bool | None = None,
        personalization_enabled: bool | None = None,
        mode: str | None = None,
        disabled_categories: list[str] | None = None,
        owner_id: str = "default_owner",
    ) -> PersonalizationSettingsState:
        if learning_enabled is not None:
            self._learning_enabled = learning_enabled
            if not learning_enabled:
                await self._audit(owner_id, PersonalizationEventType.LEARNING_PAUSED, "system", {}, "Learning paused by user")
            else:
                await self._audit(owner_id, PersonalizationEventType.LEARNING_RESUMED, "system", {}, "Learning resumed by user")

        if personalization_enabled is not None:
            self._personalization_enabled = personalization_enabled

        if mode is not None:
            self._learning_mode = LearningMode(mode.upper())
            self.hypothesis_engine.mode = self._learning_mode

        if disabled_categories is not None:
            self._disabled_categories = {c.upper() for c in disabled_categories}

        return self.get_settings_state()

    # ------------------------------------------------------------------
    # Ingestion & Learning Pipeline
    # ------------------------------------------------------------------

    async def ingest_signal(self, signal: LearningSignal) -> tuple[LearningObservation | None, PreferenceHypothesis | None, Preference | None]:
        """Process incoming learning signal through observation -> hypothesis -> preference pipeline."""
        await self.signal_repo.save(signal)

        if not self._learning_enabled or self._learning_mode == LearningMode.OFF:
            logger.info("Learning is disabled. Signal %s saved without processing.", signal.signal_id)
            return None, None, None

        # 1. Infer observation
        observation = await self.inference_provider.infer_observation(signal)
        if observation is None:
            return None, None, None

        await self.observation_repo.save(observation)

        # Check disabled category
        category = str(observation.features.get("category", "")).upper()
        if category in self._disabled_categories:
            logger.info("Category %s is disabled. Discarding observation.", category)
            return observation, None, None

        # 2. Process hypothesis & preference promotion
        hypothesis, promoted_pref = await self.hypothesis_engine.process_observation(
            signal=signal, observation=observation, owner_id=signal.owner_id
        )

        if hypothesis:
            await self._audit(
                signal.owner_id,
                PersonalizationEventType.HYPOTHESIS_CREATED,
                hypothesis.hypothesis_id,
                {"key": hypothesis.key, "proposed_value": hypothesis.proposed_value, "confidence": hypothesis.confidence},
                f"Hypothesis created/updated from signal {signal.signal_id}",
            )

        if promoted_pref:
            await self._audit(
                signal.owner_id,
                PersonalizationEventType.HYPOTHESIS_PROMOTED,
                promoted_pref.preference_id,
                {"key": promoted_pref.key, "value": promoted_pref.value},
                f"Promoted hypothesis to active preference {promoted_pref.preference_id}",
            )
            # Sync user profile
            await self.profile_service.get_or_create_profile(signal.owner_id)

        return observation, hypothesis, promoted_pref

    # ------------------------------------------------------------------
    # Preference CRUD & Resolution
    # ------------------------------------------------------------------

    async def create_preference(
        self,
        owner_id: str,
        category: str,
        key: str,
        value: Any,
        source: PreferenceSource = PreferenceSource.EXPLICIT_USER,
        scope: str = "GLOBAL",
        metadata: dict[str, Any] | None = None,
    ) -> Preference:
        """Create explicit user preference."""
        self.policy_validator.validate_preference_creation(
            category=category, key=key, value=value, source_is_explicit=(source == PreferenceSource.EXPLICIT_USER)
        )

        pref = Preference(
            owner_id=owner_id,
            category=category.upper(),
            key=key,
            value=value,
            value_type=type(value).__name__,
            source=source,
            status=PreferenceStatus.ACTIVE,
            confidence=1.0,
            strength=1.0,
            metadata=metadata or {},
        )
        saved = await self.preference_repo.save(pref)

        # Record explicit evidence
        evidence = PreferenceEvidence(
            preference_id=saved.preference_id,
            source_type=source,
            source_reference="explicit_user_input",
            observation=f"Explicitly set preference '{key}' = '{value}'",
            weight=1.0,
            confidence=1.0,
        )
        await self.evidence_repo.save(evidence)

        await self._audit(
            owner_id,
            PersonalizationEventType.PREFERENCE_CREATED,
            saved.preference_id,
            {"key": key, "value": value, "source": source.value},
            "Explicit user preference created",
        )

        # Sync profile
        await self.profile_service.get_or_create_profile(owner_id)
        return saved

    async def update_preference(
        self, preference_id: str, value: Any, owner_id: str = "default_owner"
    ) -> Preference:
        """Update existing preference value."""
        pref = await self.preference_repo.get_by_id(preference_id)
        if pref is None or pref.owner_id != owner_id:
            raise PreferenceNotFoundError(f"Preference '{preference_id}' not found.")

        self.policy_validator.validate_preference_creation(
            category=pref.category, key=pref.key, value=value, source_is_explicit=True
        )

        pref.value = value
        pref.version += 1
        pref.updated_at = datetime.now(UTC)
        saved = await self.preference_repo.save(pref)

        await self._audit(
            owner_id,
            PersonalizationEventType.PREFERENCE_UPDATED,
            saved.preference_id,
            {"key": pref.key, "new_value": value},
            "Preference updated by user",
        )
        await self.profile_service.get_or_create_profile(owner_id)
        return saved

    async def delete_preference(self, preference_id: str, owner_id: str = "default_owner") -> bool:
        """Delete user preference."""
        pref = await self.preference_repo.get_by_id(preference_id)
        if pref is None or pref.owner_id != owner_id:
            raise PreferenceNotFoundError(f"Preference '{preference_id}' not found.")

        success = await self.preference_repo.delete(preference_id)
        if success:
            await self._audit(
                owner_id,
                PersonalizationEventType.PREFERENCE_REJECTED,
                preference_id,
                {"key": pref.key},
                "Preference deleted by user",
            )
            await self.profile_service.get_or_create_profile(owner_id)
        return success

    async def resolve_preference(
        self,
        category: str,
        key: str,
        owner_id: str = "default_owner",
        context: dict[str, Any] | None = None,
    ) -> ResolvedPreference:
        """Resolve effective preference value taking into account precedence and user controls."""
        if not self._personalization_enabled:
            # Fall back to default if personalization is disabled
            default_val = self.resolver._get_system_default(category.upper(), key)
            return ResolvedPreference(
                category=category.upper(),
                key=key,
                value=default_val,
                source=PreferenceSource.SYSTEM_DEFAULT,
                confidence=1.0,
                scope=PreferenceScope.GLOBAL,
                reason="Personalization subsystem is disabled. Returning system default.",
            )

        return await self.resolver.resolve(
            category=category,
            key=key,
            owner_id=owner_id,
            context=context,
            disabled_categories=list(self._disabled_categories),
        )

    # ------------------------------------------------------------------
    # Confirmation, Rejection & Correction
    # ------------------------------------------------------------------

    async def confirm_preference(self, preference_or_hypothesis_id: str, owner_id: str = "default_owner") -> Preference:
        """Confirm a pending/inferred preference or hypothesis."""
        # Try preference first
        pref = await self.preference_repo.get_by_id(preference_or_hypothesis_id)
        if pref and pref.owner_id == owner_id:
            pref.confidence = 1.0
            pref.strength = 1.0
            pref.source = PreferenceSource.USER_FEEDBACK
            pref.status = PreferenceStatus.ACTIVE
            pref.updated_at = datetime.now(UTC)
            saved = await self.preference_repo.save(pref)

            await self._audit(
                owner_id,
                PersonalizationEventType.PREFERENCE_CONFIRMED,
                saved.preference_id,
                {"key": saved.key},
                "User confirmed inferred preference",
            )
            await self.profile_service.get_or_create_profile(owner_id)
            return saved

        # Try hypothesis
        hyp = await self.hypothesis_repo.get_by_id(preference_or_hypothesis_id)
        if hyp and hyp.owner_id == owner_id:
            hyp.confidence = 1.0
            promoted = await self.hypothesis_engine.promote_hypothesis(hyp)
            await self._audit(
                owner_id,
                PersonalizationEventType.PREFERENCE_CONFIRMED,
                promoted.preference_id,
                {"key": promoted.key},
                "User confirmed hypothesis -> promoted to active preference",
            )
            await self.profile_service.get_or_create_profile(owner_id)
            return promoted

        raise PreferenceNotFoundError(f"Item '{preference_or_hypothesis_id}' not found.")

    async def reject_preference(self, preference_or_hypothesis_id: str, owner_id: str = "default_owner") -> bool:
        """Reject a preference or hypothesis."""
        pref = await self.preference_repo.get_by_id(preference_or_hypothesis_id)
        if pref and pref.owner_id == owner_id:
            pref.status = PreferenceStatus.REJECTED
            pref.updated_at = datetime.now(UTC)
            await self.preference_repo.save(pref)

            await self._audit(
                owner_id,
                PersonalizationEventType.PREFERENCE_REJECTED,
                pref.preference_id,
                {"key": pref.key},
                "User rejected preference",
            )
            await self.profile_service.get_or_create_profile(owner_id)
            return True

        hyp = await self.hypothesis_repo.get_by_id(preference_or_hypothesis_id)
        if hyp and hyp.owner_id == owner_id:
            hyp.status = HypothesisStatus.REJECTED
            hyp.updated_at = datetime.now(UTC)
            await self.hypothesis_repo.save(hyp)

            await self._audit(
                owner_id,
                PersonalizationEventType.HYPOTHESIS_REJECTED,
                hyp.hypothesis_id,
                {"key": hyp.key},
                "User rejected hypothesis",
            )
            return True

        raise PreferenceNotFoundError(f"Item '{preference_or_hypothesis_id}' not found.")

    async def correct_preference(
        self,
        preference_id: str,
        correct_value: Any,
        owner_id: str = "default_owner",
        comments: str | None = None,
    ) -> Preference:
        """Explicitly correct a preference value."""
        pref = await self.preference_repo.get_by_id(preference_id)
        if pref is None or pref.owner_id != owner_id:
            raise PreferenceNotFoundError(f"Preference '{preference_id}' not found.")

        # Update preference to explicit user correction
        pref.value = correct_value
        pref.source = PreferenceSource.USER_CORRECTION
        pref.status = PreferenceStatus.ACTIVE
        pref.confidence = 1.0
        pref.strength = 1.0
        pref.version += 1
        pref.updated_at = datetime.now(UTC)
        saved = await self.preference_repo.save(pref)

        # Record evidence
        evidence = PreferenceEvidence(
            preference_id=saved.preference_id,
            source_type=PreferenceSource.USER_CORRECTION,
            source_reference="user_correction",
            observation=f"Explicit correction: {comments or 'User provided correct value'}",
            weight=1.0,
            confidence=1.0,
        )
        await self.evidence_repo.save(evidence)

        # Record feedback
        feedback = PersonalizationFeedback(
            owner_id=owner_id,
            preference_id=saved.preference_id,
            feedback_type="CORRECTION",
            comments=comments or f"Corrected to {correct_value}",
        )
        await self.feedback_repo.save(feedback)

        await self._audit(
            owner_id,
            PersonalizationEventType.PREFERENCE_CORRECTED,
            saved.preference_id,
            {"key": saved.key, "new_value": correct_value},
            "User explicitly corrected preference",
        )

        await self.profile_service.get_or_create_profile(owner_id)
        return saved

    # ------------------------------------------------------------------
    # Data Controls (Reset, Rollback)
    # ------------------------------------------------------------------

    async def reset_inferred_preferences(self, owner_id: str = "default_owner") -> int:
        """Reset/archive all inferred preferences for owner while preserving explicit preferences."""
        count = await self.preference_repo.delete_inferred_by_owner(owner_id)
        await self._audit(
            owner_id,
            PersonalizationEventType.PERSONALIZATION_RESET,
            owner_id,
            {"deleted_inferred_count": count},
            "Reset all inferred preferences",
        )
        await self.profile_service.get_or_create_profile(owner_id)
        return count

    async def reset_category(self, category: str, owner_id: str = "default_owner") -> int:
        """Reset all preferences in a specific category."""
        category_upper = category.upper()
        preferences = await self.preference_repo.list_by_owner(owner_id=owner_id, category=category_upper)
        count = 0
        for p in preferences:
            await self.preference_repo.delete(p.preference_id)
            count += 1

        await self._audit(
            owner_id,
            PersonalizationEventType.CATEGORY_RESET,
            category_upper,
            {"deleted_count": count},
            f"Reset all preferences in category '{category_upper}'",
        )
        await self.profile_service.get_or_create_profile(owner_id)
        return count

    # ------------------------------------------------------------------
    # Dry Run & Simulation
    # ------------------------------------------------------------------

    async def simulate(self, signal: LearningSignal) -> PersonalizationSimulationResult:
        """Evaluate a signal dry-run without modifying persistent state."""
        observation = await self.inference_provider.infer_observation(signal)
        if observation is None:
            return PersonalizationSimulationResult(
                signal=signal,
                observation=None,
                hypothesis=None,
                confidence=0.0,
                potential_preference=None,
                resolution=None,
                reason="Signal did not yield any recognized behavioral observation pattern.",
            )

        features = observation.features
        category = str(features.get("category", "COMMUNICATION")).upper()
        key = str(features.get("key", "detail_level"))
        proposed_value = features.get("proposed_value")

        # Validate safety
        try:
            self.policy_validator.validate_hypothesis(
                category=category, key=key, proposed_value=proposed_value, raise_on_violation=True
            )
        except Exception as exc:
            return PersonalizationSimulationResult(
                signal=signal,
                observation=observation,
                hypothesis=None,
                confidence=0.0,
                potential_preference=None,
                resolution=None,
                reason=f"Policy validation rejected signal: {str(exc)}",
            )

        mock_hypothesis = PreferenceHypothesis(
            owner_id=signal.owner_id,
            category=category,
            key=key,
            proposed_value=proposed_value,
            confidence=observation.confidence,
            evidence_count=1,
            status=HypothesisStatus.NEW,
        )

        mock_pref: Preference | None = None
        if observation.confidence >= self.settings.min_confidence:
            mock_pref = Preference(
                owner_id=signal.owner_id,
                category=category,
                key=key,
                value=proposed_value,
                source=PreferenceSource.OBSERVED_BEHAVIOR,
                confidence=observation.confidence,
            )

        # Simulate resolution
        resolution = await self.resolver.resolve(
            category=category, key=key, owner_id=signal.owner_id
        )

        return PersonalizationSimulationResult(
            signal=signal,
            observation=observation,
            hypothesis=mock_hypothesis,
            confidence=observation.confidence,
            potential_preference=mock_pref,
            resolution=resolution,
            reason="Simulation completed cleanly.",
        )

    # ------------------------------------------------------------------
    # Audit Helper
    # ------------------------------------------------------------------

    async def _audit(
        self,
        owner_id: str,
        event_type: PersonalizationEventType,
        target_id: str,
        changes: dict[str, Any],
        reason: str,
    ) -> None:
        entry = PersonalizationHistoryEntry(
            owner_id=owner_id,
            event_type=event_type,
            target_id=target_id,
            changes=changes,
            reason=reason,
        )
        await self.history_repo.save(entry)
