"""Confidence evaluator managing evidence weights, reinforcement, and decay for Module 31."""

from collections.abc import Sequence
from datetime import UTC, datetime

from max.personalization.domain.enums import PreferenceSource
from max.personalization.domain.models import Preference, PreferenceEvidence

SOURCE_WEIGHTS: dict[PreferenceSource, float] = {
    PreferenceSource.EXPLICIT_USER: 1.0,
    PreferenceSource.USER_CORRECTION: 1.0,
    PreferenceSource.USER_FEEDBACK: 0.8,
    PreferenceSource.PROACTIVE_FEEDBACK: 0.7,
    PreferenceSource.CONVERSATION: 0.6,
    PreferenceSource.OBSERVED_BEHAVIOR: 0.5,
    PreferenceSource.TASK_HISTORY: 0.5,
    PreferenceSource.NOTIFICATION_HISTORY: 0.5,
    PreferenceSource.AUTOMATION_HISTORY: 0.5,
    PreferenceSource.SYSTEM_DEFAULT: 0.1,
}


class ConfidenceEvaluator:
    """Calculates and updates confidence for hypotheses and inferred preferences."""

    def __init__(self, default_decay_rate: float = 0.05) -> None:
        self.default_decay_rate = default_decay_rate

    def get_source_weight(self, source: PreferenceSource) -> float:
        """Retrieve standard weight for a given evidence source."""
        return SOURCE_WEIGHTS.get(source, 0.5)

    def reinforce(self, current_confidence: float, source: PreferenceSource, evidence_weight: float = 1.0) -> float:
        """Reinforce confidence using sub-linear bounded increment."""
        src_weight = self.get_source_weight(source)
        factor = 0.25 * src_weight * max(0.1, min(2.0, evidence_weight))
        new_conf = current_confidence + (1.0 - current_confidence) * factor
        return round(min(1.0, max(0.0, new_conf)), 4)

    def weaken(self, current_confidence: float, source: PreferenceSource, evidence_weight: float = 1.0) -> float:
        """Weaken confidence based on contradictory evidence."""
        src_weight = self.get_source_weight(source)
        factor = 0.3 * src_weight * max(0.1, min(2.0, evidence_weight))
        new_conf = current_confidence - factor
        return round(max(0.0, new_conf), 4)

    def evaluate_hypothesis_confidence(
        self,
        supporting_evidence: Sequence[PreferenceEvidence],
        contradicting_evidence: Sequence[PreferenceEvidence],
    ) -> float:
        """Evaluate overall confidence score from collections of supporting and contradicting evidence."""
        if not supporting_evidence:
            return 0.0

        support_score = 0.0
        for ev in supporting_evidence:
            weight = self.get_source_weight(ev.source_type) * ev.weight
            support_score += weight

        contradict_score = 0.0
        for ev in contradicting_evidence:
            weight = self.get_source_weight(ev.source_type) * ev.weight
            contradict_score += weight

        # Sub-linear saturation for support count
        base_confidence = 1.0 - (1.0 / (1.0 + 0.4 * support_score))

        # Penalty for contradictory evidence
        penalty = 0.35 * contradict_score
        final_conf = max(0.0, base_confidence - penalty)

        return round(min(1.0, final_conf), 4)

    def apply_decay(
        self, preference: Preference, current_time: datetime | None = None, decay_rate: float | None = None
    ) -> Preference:
        """Apply time-based confidence decay to an inferred preference."""
        # Explicit user preferences NEVER decay silently!
        if preference.source == PreferenceSource.EXPLICIT_USER:
            return preference

        rate = decay_rate if decay_rate is not None else self.default_decay_rate
        now = current_time or datetime.now(UTC)
        days_elapsed = (now - preference.updated_at).total_seconds() / 86400.0

        if days_elapsed <= 0:
            return preference

        decay_amount = rate * days_elapsed
        new_confidence = max(0.0, preference.confidence - decay_amount)
        new_strength = max(0.0, preference.strength - decay_amount)

        preference.confidence = round(new_confidence, 4)
        preference.strength = round(new_strength, 4)
        return preference
