"""In-memory repository implementations for Module 31 — Learning & Personalization Engine."""


from max.personalization.domain.enums import PreferenceSource, PreferenceStatus
from max.personalization.domain.models import (
    LearningObservation,
    LearningSignal,
    PersonalizationFeedback,
    PersonalizationHistoryEntry,
    PersonalizationProfile,
    Preference,
    PreferenceEvidence,
    PreferenceHypothesis,
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


class InMemoryPreferenceRepository(PreferenceRepository):
    """In-memory store for user preferences."""

    def __init__(self) -> None:
        self._preferences: dict[str, Preference] = {}

    async def save(self, preference: Preference) -> Preference:
        self._preferences[preference.preference_id] = preference
        return preference

    async def get_by_id(self, preference_id: str) -> Preference | None:
        return self._preferences.get(preference_id)

    async def list_by_owner(
        self,
        owner_id: str,
        category: str | None = None,
        key: str | None = None,
        active_only: bool = True,
    ) -> list[Preference]:
        results: list[Preference] = []
        for p in self._preferences.values():
            if p.owner_id != owner_id:
                continue
            if active_only and p.status != PreferenceStatus.ACTIVE:
                continue
            if category and p.category.upper() != category.upper():
                continue
            if key and p.key != key:
                continue
            results.append(p)
        return results

    async def delete(self, preference_id: str) -> bool:
        if preference_id in self._preferences:
            del self._preferences[preference_id]
            return True
        return False

    async def delete_inferred_by_owner(self, owner_id: str, category: str | None = None) -> int:
        to_delete: list[str] = []
        for p_id, p in self._preferences.items():
            if p.owner_id == owner_id and p.source != PreferenceSource.EXPLICIT_USER:
                if category is None or p.category.upper() == category.upper():
                    to_delete.append(p_id)

        for p_id in to_delete:
            del self._preferences[p_id]
        return len(to_delete)


class InMemoryPreferenceEvidenceRepository(PreferenceEvidenceRepository):
    """In-memory store for preference evidence."""

    def __init__(self) -> None:
        self._evidence: dict[str, PreferenceEvidence] = {}

    async def save(self, evidence: PreferenceEvidence) -> PreferenceEvidence:
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    async def list_by_preference(self, preference_id: str) -> list[PreferenceEvidence]:
        return [e for e in self._evidence.values() if e.preference_id == preference_id]

    async def list_by_hypothesis(self, hypothesis_id: str) -> list[PreferenceEvidence]:
        return [e for e in self._evidence.values() if e.hypothesis_id == hypothesis_id]


class InMemoryLearningSignalRepository(LearningSignalRepository):
    """In-memory store for raw learning signals."""

    def __init__(self) -> None:
        self._signals: dict[str, LearningSignal] = {}

    async def save(self, signal: LearningSignal) -> LearningSignal:
        self._signals[signal.signal_id] = signal
        return signal

    async def get_by_id(self, signal_id: str) -> LearningSignal | None:
        return self._signals.get(signal_id)

    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[LearningSignal]:
        signals = [s for s in self._signals.values() if s.owner_id == owner_id]
        signals.sort(key=lambda s: s.observed_at, reverse=True)
        return signals[:limit]


class InMemoryObservationRepository(ObservationRepository):
    """In-memory store for derived observations."""

    def __init__(self) -> None:
        self._observations: dict[str, LearningObservation] = {}

    async def save(self, observation: LearningObservation) -> LearningObservation:
        self._observations[observation.observation_id] = observation
        return observation

    async def list_by_signal(self, signal_id: str) -> list[LearningObservation]:
        return [o for o in self._observations.values() if o.signal_id == signal_id]


class InMemoryHypothesisRepository(HypothesisRepository):
    """In-memory store for preference hypotheses."""

    def __init__(self) -> None:
        self._hypotheses: dict[str, PreferenceHypothesis] = {}

    async def save(self, hypothesis: PreferenceHypothesis) -> PreferenceHypothesis:
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis
        return hypothesis

    async def get_by_id(self, hypothesis_id: str) -> PreferenceHypothesis | None:
        return self._hypotheses.get(hypothesis_id)

    async def find_matching(
        self, owner_id: str, category: str, key: str, proposed_value: str
    ) -> PreferenceHypothesis | None:
        for h in self._hypotheses.values():
            if (
                h.owner_id == owner_id
                and h.category.upper() == category.upper()
                and h.key == key
                and str(h.proposed_value) == str(proposed_value)
            ):
                return h
        return None

    async def list_by_owner(self, owner_id: str, category: str | None = None) -> list[PreferenceHypothesis]:
        results = []
        for h in self._hypotheses.values():
            if h.owner_id == owner_id:
                if category is None or h.category.upper() == category.upper():
                    results.append(h)
        return results

    async def delete(self, hypothesis_id: str) -> bool:
        if hypothesis_id in self._hypotheses:
            del self._hypotheses[hypothesis_id]
            return True
        return False


class InMemoryPersonalizationProfileRepository(PersonalizationProfileRepository):
    """In-memory store for personalization profiles."""

    def __init__(self) -> None:
        self._profiles: dict[str, PersonalizationProfile] = {}

    async def save(self, profile: PersonalizationProfile) -> PersonalizationProfile:
        self._profiles[profile.owner_id] = profile
        return profile

    async def get_by_owner(self, owner_id: str) -> PersonalizationProfile | None:
        return self._profiles.get(owner_id)


class InMemoryFeedbackRepository(FeedbackRepository):
    """In-memory store for user feedback."""

    def __init__(self) -> None:
        self._feedback: list[PersonalizationFeedback] = []

    async def save(self, feedback: PersonalizationFeedback) -> PersonalizationFeedback:
        self._feedback.append(feedback)
        return feedback

    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[PersonalizationFeedback]:
        items = [f for f in self._feedback if f.owner_id == owner_id]
        items.sort(key=lambda f: f.created_at, reverse=True)
        return items[:limit]


class InMemoryPersonalizationHistoryRepository(PersonalizationHistoryRepository):
    """In-memory store for personalization audit logs."""

    def __init__(self) -> None:
        self._entries: list[PersonalizationHistoryEntry] = []

    async def save(self, entry: PersonalizationHistoryEntry) -> PersonalizationHistoryEntry:
        self._entries.append(entry)
        return entry

    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[PersonalizationHistoryEntry]:
        items = [e for e in self._entries if e.owner_id == owner_id]
        items.sort(key=lambda e: e.timestamp, reverse=True)
        return items[:limit]
