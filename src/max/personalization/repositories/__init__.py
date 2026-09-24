"""Repositories package for Module 31 — Learning & Personalization Engine."""

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

__all__ = [
    "PreferenceRepository",
    "PreferenceEvidenceRepository",
    "LearningSignalRepository",
    "ObservationRepository",
    "HypothesisRepository",
    "PersonalizationProfileRepository",
    "FeedbackRepository",
    "PersonalizationHistoryRepository",
    "InMemoryPreferenceRepository",
    "InMemoryPreferenceEvidenceRepository",
    "InMemoryLearningSignalRepository",
    "InMemoryObservationRepository",
    "InMemoryHypothesisRepository",
    "InMemoryPersonalizationProfileRepository",
    "InMemoryFeedbackRepository",
    "InMemoryPersonalizationHistoryRepository",
]
