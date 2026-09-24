"""Dependency Injection container for Module 31 — Learning & Personalization Engine."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.personalization.adapters.adapters import (
    ConversationIntegrationAdapter,
    KnowledgeIntegrationAdapter,
    MemoryIntegrationAdapter,
    NotificationPersonalizationAdapter,
    PermissionGateAdapter,
    PersonalizationContextSource,
    ProactivePersonalizationAdapter,
    SchedulerPersonalizationAdapter,
    ToolRankingAdapter,
    UserProfileAdapter,
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

logger = logging.getLogger(__name__)


class PersonalizationContainer:
    """Dependency Injection container managing components of Module 31."""

    _instance: PersonalizationContainer | None = None

    def __init__(self) -> None:
        self.settings = get_settings().personalization

        # Repositories
        self.preference_repo = InMemoryPreferenceRepository()
        self.evidence_repo = InMemoryPreferenceEvidenceRepository()
        self.signal_repo = InMemoryLearningSignalRepository()
        self.observation_repo = InMemoryObservationRepository()
        self.hypothesis_repo = InMemoryHypothesisRepository()
        self.profile_repo = InMemoryPersonalizationProfileRepository()
        self.feedback_repo = InMemoryFeedbackRepository()
        self.history_repo = InMemoryPersonalizationHistoryRepository()

        # Orchestration Service
        self.service = PersonalizationService(
            settings=self.settings,
            preference_repo=self.preference_repo,
            evidence_repo=self.evidence_repo,
            signal_repo=self.signal_repo,
            observation_repo=self.observation_repo,
            hypothesis_repo=self.hypothesis_repo,
            profile_repo=self.profile_repo,
            feedback_repo=self.feedback_repo,
            history_repo=self.history_repo,
        )

        # Integration Adapters
        self.context_source = PersonalizationContextSource(self.service)
        self.user_profile_adapter = UserProfileAdapter()
        self.conversation_adapter = ConversationIntegrationAdapter(self.service)
        self.memory_adapter = MemoryIntegrationAdapter()
        self.knowledge_adapter = KnowledgeIntegrationAdapter()
        self.tool_ranking_adapter = ToolRankingAdapter(self.service)
        self.permission_adapter = PermissionGateAdapter()
        self.notification_adapter = NotificationPersonalizationAdapter(self.service)
        self.scheduler_adapter = SchedulerPersonalizationAdapter(self.service)
        self.proactive_adapter = ProactivePersonalizationAdapter(self.service)

    @classmethod
    def get_instance(cls) -> PersonalizationContainer:
        """Get or create singleton instance of PersonalizationContainer."""
        if cls._instance is None:
            cls._instance = PersonalizationContainer()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (primarily for test isolation)."""
        cls._instance = None
