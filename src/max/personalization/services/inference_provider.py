"""Inference provider abstraction and safety wrappers for Module 31."""

from abc import ABC, abstractmethod

from max.personalization.domain.models import LearningObservation, LearningSignal
from max.personalization.services.pattern_detector import PatternDetector
from max.personalization.services.policy_validator import PolicyValidator


class PersonalizationInferenceProvider(ABC):
    """Abstract provider for generating personalization observations."""

    @abstractmethod
    async def infer_observation(self, signal: LearningSignal) -> LearningObservation | None:
        """Infer structured behavioral observation from incoming signal."""


class DeterministicPersonalizationProvider(PersonalizationInferenceProvider):
    """Rule-based statistical/deterministic provider for development, testing, and runtime core."""

    def __init__(self, pattern_detector: PatternDetector) -> None:
        self.pattern_detector = pattern_detector

    async def infer_observation(self, signal: LearningSignal) -> LearningObservation | None:
        return self.pattern_detector.detect_observation(signal)


class ValidatedAIInferenceProvider(PersonalizationInferenceProvider):
    """AI-assisted inference wrapper enforcing strict policy validation boundaries."""

    def __init__(
        self,
        raw_ai_provider: PersonalizationInferenceProvider,
        policy_validator: PolicyValidator,
    ) -> None:
        self.raw_ai_provider = raw_ai_provider
        self.policy_validator = policy_validator

    async def infer_observation(self, signal: LearningSignal) -> LearningObservation | None:
        obs = await self.raw_ai_provider.infer_observation(signal)
        if obs is None:
            return None

        # Filter AI output through PolicyValidator
        features = obs.features
        cat = str(features.get("category", "COMMUNICATION"))
        key = str(features.get("key", ""))
        val = features.get("proposed_value")

        is_valid = self.policy_validator.validate_hypothesis(
            category=cat,
            key=key,
            proposed_value=val,
            observation=f"AI inference from signal {signal.signal_id}",
            raise_on_violation=False,
        )

        if not is_valid:
            return None

        return obs
