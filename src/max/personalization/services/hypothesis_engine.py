"""Hypothesis engine managing lifecycle and promotion of inferred preferences for Module 31."""

import logging
from datetime import UTC, datetime

from max.personalization.domain.enums import (
    HypothesisStatus,
    LearningMode,
    PreferenceSource,
    PreferenceStatus,
)
from max.personalization.domain.models import (
    LearningObservation,
    LearningSignal,
    Preference,
    PreferenceEvidence,
    PreferenceHypothesis,
)
from max.personalization.repositories.interfaces import (
    HypothesisRepository,
    PreferenceEvidenceRepository,
    PreferenceRepository,
)
from max.personalization.services.confidence_evaluator import ConfidenceEvaluator
from max.personalization.services.policy_validator import PolicyValidator

logger = logging.getLogger(__name__)


class HypothesisEngine:
    """Manages the creation, strengthening, weakening, and promotion of preference hypotheses."""

    def __init__(
        self,
        hypothesis_repo: HypothesisRepository,
        evidence_repo: PreferenceEvidenceRepository,
        preference_repo: PreferenceRepository,
        policy_validator: PolicyValidator,
        confidence_evaluator: ConfidenceEvaluator,
        min_confidence: float = 0.7,
        min_evidence: int = 3,
        mode: LearningMode = LearningMode.ADAPTIVE,
    ) -> None:
        self.hypothesis_repo = hypothesis_repo
        self.evidence_repo = evidence_repo
        self.preference_repo = preference_repo
        self.policy_validator = policy_validator
        self.confidence_evaluator = confidence_evaluator
        self.min_confidence = min_confidence
        self.min_evidence = min_evidence
        self.mode = mode

    async def process_observation(
        self,
        signal: LearningSignal,
        observation: LearningObservation,
        owner_id: str = "default_owner",
    ) -> tuple[PreferenceHypothesis | None, Preference | None]:
        """Ingest an observation, update or create hypothesis, and check for preference promotion."""
        if self.mode == LearningMode.OFF:
            logger.info("Learning mode is OFF. Discarding observation.")
            return None, None

        features = observation.features
        category = str(features.get("category", "COMMUNICATION")).upper()
        key = str(features.get("key", ""))
        proposed_value = features.get("proposed_value")
        is_explicit = bool(features.get("is_explicit", False))
        is_correction = bool(features.get("is_correction", False))

        if not key or proposed_value is None:
            return None, None

        # 1. Validate safety boundaries
        self.policy_validator.validate_hypothesis(
            category=category,
            key=key,
            proposed_value=proposed_value,
            observation=f"Signal {signal.signal_id} ({signal.signal_type})",
            raise_on_violation=True,
        )

        # 2. Handle Explicit User Preferences or Corrections directly
        if is_explicit or is_correction:
            pref_source = (
                PreferenceSource.USER_CORRECTION if is_correction else PreferenceSource.EXPLICIT_USER
            )
            created_pref = await self._create_explicit_preference(
                owner_id=owner_id,
                category=category,
                key=key,
                value=proposed_value,
                source=pref_source,
                observation=f"Explicit statement from signal {signal.signal_id}",
            )
            return None, created_pref

        # 3. Mode check: EXPLICIT_ONLY discards implicit inferred observations
        if self.mode == LearningMode.EXPLICIT_ONLY:
            logger.info("Learning mode is EXPLICIT_ONLY. Ignoring implicit observation.")
            return None, None

        # 4. Check existing hypothesis matching owner, category, key, proposed_value
        existing_h = await self.hypothesis_repo.find_matching(
            owner_id=owner_id, category=category, key=key, proposed_value=str(proposed_value)
        )

        source_type = PreferenceSource.OBSERVED_BEHAVIOR
        evidence = PreferenceEvidence(
            source_type=source_type,
            source_reference=signal.signal_id,
            observation=f"Observation pattern: {observation.pattern_type}",
            weight=1.0,
            confidence=observation.confidence,
        )

        if existing_h is None:
            # Create new hypothesis
            hypothesis = PreferenceHypothesis(
                owner_id=owner_id,
                category=category,
                key=key,
                proposed_value=proposed_value,
                value_type=type(proposed_value).__name__,
                confidence=observation.confidence,
                evidence_count=1,
                status=HypothesisStatus.NEW,
            )
            hypothesis = await self.hypothesis_repo.save(hypothesis)
            evidence.hypothesis_id = hypothesis.hypothesis_id
            evidence = await self.evidence_repo.save(evidence)
            hypothesis.supporting_evidence.append(evidence.evidence_id)
            hypothesis = await self.hypothesis_repo.save(hypothesis)
        else:
            # Update existing hypothesis
            hypothesis = existing_h
            evidence.hypothesis_id = hypothesis.hypothesis_id
            evidence = await self.evidence_repo.save(evidence)
            hypothesis.supporting_evidence.append(evidence.evidence_id)
            hypothesis.evidence_count = len(hypothesis.supporting_evidence)

            # Recalculate confidence
            new_conf = self.confidence_evaluator.reinforce(
                current_confidence=hypothesis.confidence,
                source=source_type,
                evidence_weight=evidence.weight,
            )
            hypothesis.confidence = new_conf

            if hypothesis.status == HypothesisStatus.NEW and hypothesis.evidence_count >= 2:
                hypothesis.status = HypothesisStatus.STRENGTHENING
            elif hypothesis.evidence_count >= self.min_evidence and hypothesis.confidence >= self.min_confidence:
                hypothesis.status = HypothesisStatus.STABLE

            hypothesis.updated_at = datetime.now(UTC)
            hypothesis = await self.hypothesis_repo.save(hypothesis)

        # 5. Evaluate promotion if mode allows ADAPTIVE promotion
        promoted_pref: Preference | None = None
        if self.mode == LearningMode.ADAPTIVE:
            if (
                hypothesis.confidence >= self.min_confidence
                and hypothesis.evidence_count >= self.min_evidence
                and hypothesis.status not in (HypothesisStatus.CONFLICTED, HypothesisStatus.REJECTED, HypothesisStatus.PROMOTED)
            ):
                promoted_pref = await self.promote_hypothesis(hypothesis)

        return hypothesis, promoted_pref

    async def promote_hypothesis(self, hypothesis: PreferenceHypothesis) -> Preference:
        """Promote a sufficiently supported hypothesis into an active learned preference."""
        # Double check safety before promotion
        self.policy_validator.validate_hypothesis(
            category=hypothesis.category,
            key=hypothesis.key,
            proposed_value=hypothesis.proposed_value,
            raise_on_violation=True,
        )

        preference = Preference(
            owner_id=hypothesis.owner_id,
            category=hypothesis.category,
            key=hypothesis.key,
            value=hypothesis.proposed_value,
            value_type=hypothesis.value_type,
            source=PreferenceSource.OBSERVED_BEHAVIOR,
            status=PreferenceStatus.ACTIVE,
            confidence=hypothesis.confidence,
            strength=0.8,
            version=1,
            metadata={"promoted_from_hypothesis": hypothesis.hypothesis_id},
        )
        saved_pref = await self.preference_repo.save(preference)

        hypothesis.status = HypothesisStatus.PROMOTED
        hypothesis.updated_at = datetime.now(UTC)
        await self.hypothesis_repo.save(hypothesis)

        logger.info(
            "Promoted hypothesis %s to active preference %s (key=%s)",
            hypothesis.hypothesis_id,
            saved_pref.preference_id,
            saved_pref.key,
        )
        return saved_pref

    async def _create_explicit_preference(
        self,
        owner_id: str,
        category: str,
        key: str,
        value: str,
        source: PreferenceSource,
        observation: str,
    ) -> Preference:
        # Check if existing active explicit preference exists for key
        existing_list = await self.preference_repo.list_by_owner(
            owner_id=owner_id, category=category, key=key, active_only=True
        )

        for old_p in existing_list:
            if old_p.source != PreferenceSource.EXPLICIT_USER and source == PreferenceSource.USER_CORRECTION:
                # User explicit correction overrides and disables previous inferred preferences
                old_p.status = PreferenceStatus.REJECTED
                old_p.updated_at = datetime.now(UTC)
                await self.preference_repo.save(old_p)
            elif old_p.source == PreferenceSource.EXPLICIT_USER and source == PreferenceSource.EXPLICIT_USER:
                # Update existing explicit preference
                old_p.value = value
                old_p.updated_at = datetime.now(UTC)
                old_p.version += 1
                return await self.preference_repo.save(old_p)

        pref = Preference(
            owner_id=owner_id,
            category=category,
            key=key,
            value=value,
            value_type=type(value).__name__,
            source=source,
            status=PreferenceStatus.ACTIVE,
            confidence=1.0,
            strength=1.0,
            version=1,
        )
        saved = await self.preference_repo.save(pref)

        # Record evidence
        evidence = PreferenceEvidence(
            preference_id=saved.preference_id,
            source_type=source,
            source_reference="explicit_statement",
            observation=observation,
            weight=1.0,
            confidence=1.0,
        )
        await self.evidence_repo.save(evidence)

        # Also weaken/reject any conflicting hypotheses
        hypotheses = await self.hypothesis_repo.list_by_owner(owner_id=owner_id, category=category)
        for h in hypotheses:
            if h.key == key and str(h.proposed_value) != str(value):
                h.status = HypothesisStatus.REJECTED
                h.updated_at = datetime.now(UTC)
                await self.hypothesis_repo.save(h)

        return saved
