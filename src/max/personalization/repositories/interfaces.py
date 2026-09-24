"""Repository interfaces for Module 31 — Learning & Personalization Engine."""

from abc import ABC, abstractmethod

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


class PreferenceRepository(ABC):
    """Abstract interface for user preferences persistence."""

    @abstractmethod
    async def save(self, preference: Preference) -> Preference:
        """Save or update a preference."""

    @abstractmethod
    async def get_by_id(self, preference_id: str) -> Preference | None:
        """Get preference by unique ID."""

    @abstractmethod
    async def list_by_owner(
        self,
        owner_id: str,
        category: str | None = None,
        key: str | None = None,
        active_only: bool = True,
    ) -> list[Preference]:
        """List preferences matching owner and criteria."""

    @abstractmethod
    async def delete(self, preference_id: str) -> bool:
        """Delete preference by ID."""

    @abstractmethod
    async def delete_inferred_by_owner(self, owner_id: str, category: str | None = None) -> int:
        """Delete or archive inferred preferences for owner."""


class PreferenceEvidenceRepository(ABC):
    """Abstract interface for preference evidence persistence."""

    @abstractmethod
    async def save(self, evidence: PreferenceEvidence) -> PreferenceEvidence:
        """Save evidence entry."""

    @abstractmethod
    async def list_by_preference(self, preference_id: str) -> list[PreferenceEvidence]:
        """List evidence linked to a preference."""

    @abstractmethod
    async def list_by_hypothesis(self, hypothesis_id: str) -> list[PreferenceEvidence]:
        """List evidence linked to a hypothesis."""


class LearningSignalRepository(ABC):
    """Abstract interface for learning signals persistence."""

    @abstractmethod
    async def save(self, signal: LearningSignal) -> LearningSignal:
        """Save a learning signal."""

    @abstractmethod
    async def get_by_id(self, signal_id: str) -> LearningSignal | None:
        """Get signal by ID."""

    @abstractmethod
    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[LearningSignal]:
        """List signals for owner."""


class ObservationRepository(ABC):
    """Abstract interface for behavioral observations persistence."""

    @abstractmethod
    async def save(self, observation: LearningObservation) -> LearningObservation:
        """Save an observation."""

    @abstractmethod
    async def list_by_signal(self, signal_id: str) -> list[LearningObservation]:
        """List observations derived from a signal."""


class HypothesisRepository(ABC):
    """Abstract interface for preference hypotheses persistence."""

    @abstractmethod
    async def save(self, hypothesis: PreferenceHypothesis) -> PreferenceHypothesis:
        """Save or update a hypothesis."""

    @abstractmethod
    async def get_by_id(self, hypothesis_id: str) -> PreferenceHypothesis | None:
        """Get hypothesis by ID."""

    @abstractmethod
    async def find_matching(
        self, owner_id: str, category: str, key: str, proposed_value: str
    ) -> PreferenceHypothesis | None:
        """Find active hypothesis matching owner, category, key, proposed_value."""

    @abstractmethod
    async def list_by_owner(self, owner_id: str, category: str | None = None) -> list[PreferenceHypothesis]:
        """List hypotheses for owner."""

    @abstractmethod
    async def delete(self, hypothesis_id: str) -> bool:
        """Delete hypothesis by ID."""


class PersonalizationProfileRepository(ABC):
    """Abstract interface for personalization profile persistence."""

    @abstractmethod
    async def save(self, profile: PersonalizationProfile) -> PersonalizationProfile:
        """Save or update a profile."""

    @abstractmethod
    async def get_by_owner(self, owner_id: str) -> PersonalizationProfile | None:
        """Get profile by owner ID."""


class FeedbackRepository(ABC):
    """Abstract interface for personalization feedback persistence."""

    @abstractmethod
    async def save(self, feedback: PersonalizationFeedback) -> PersonalizationFeedback:
        """Save user feedback."""

    @abstractmethod
    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[PersonalizationFeedback]:
        """List feedback for owner."""


class PersonalizationHistoryRepository(ABC):
    """Abstract interface for audit history persistence."""

    @abstractmethod
    async def save(self, entry: PersonalizationHistoryEntry) -> PersonalizationHistoryEntry:
        """Save audit history entry."""

    @abstractmethod
    async def list_by_owner(self, owner_id: str, limit: int = 100) -> list[PersonalizationHistoryEntry]:
        """List audit entries for owner."""
