"""Preference decay service for Module 31."""

import logging
from datetime import UTC, datetime

from max.personalization.domain.enums import PreferenceSource, PreferenceStatus
from max.personalization.repositories.interfaces import PreferenceRepository
from max.personalization.services.confidence_evaluator import ConfidenceEvaluator

logger = logging.getLogger(__name__)


class PreferenceDecayService:
    """Service executing time-based confidence decay for inferred preferences."""

    def __init__(
        self,
        preference_repo: PreferenceRepository,
        confidence_evaluator: ConfidenceEvaluator,
        decay_rate: float = 0.05,
        min_confidence_cutoff: float = 0.3,
    ) -> None:
        self.preference_repo = preference_repo
        self.confidence_evaluator = confidence_evaluator
        self.decay_rate = decay_rate
        self.min_confidence_cutoff = min_confidence_cutoff

    async def run_decay_cycle(
        self, owner_id: str = "default_owner", current_time: datetime | None = None
    ) -> tuple[int, int]:
        """Run decay cycle across active preferences for owner. Returns (decayed_count, expired_count)."""
        now = current_time or datetime.now(UTC)
        preferences = await self.preference_repo.list_by_owner(
            owner_id=owner_id, active_only=True
        )

        decayed_count = 0
        expired_count = 0

        for pref in preferences:
            # Skip explicit preferences!
            if pref.source in (PreferenceSource.EXPLICIT_USER, PreferenceSource.USER_CORRECTION):
                continue

            old_conf = pref.confidence
            decayed_pref = self.confidence_evaluator.apply_decay(
                pref, current_time=now, decay_rate=self.decay_rate
            )

            if decayed_pref.confidence < old_conf:
                decayed_count += 1

            if decayed_pref.confidence < self.min_confidence_cutoff:
                decayed_pref.status = PreferenceStatus.EXPIRED
                decayed_pref.updated_at = now
                expired_count += 1
                logger.info(
                    "Preference %s (key=%s) expired due to confidence decay (confidence=%.4f < %.2f)",
                    decayed_pref.preference_id,
                    decayed_pref.key,
                    decayed_pref.confidence,
                    self.min_confidence_cutoff,
                )

            await self.preference_repo.save(decayed_pref)

        return decayed_count, expired_count
