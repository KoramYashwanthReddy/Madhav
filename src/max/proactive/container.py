"""Dependency Injection container for Module 30 — Proactive Intelligence Engine."""

from __future__ import annotations

import logging

from max.config.settings import get_settings
from max.proactive.adapters.adapters import (
    ContextMemoryKnowledgeAdapter,
    ExternalIntegrationAdapter,
    NotificationSystemAdapter,
    PermissionGateAdapter,
    SchedulerIntegrationAdapter,
    TaskIntegrationAdapter,
    UserProfileAdapter,
)
from max.proactive.domain.enums import ProactiveMode
from max.proactive.repositories.repositories import (
    InMemoryActionRepository,
    InMemoryAuditRepository,
    InMemoryCandidateRepository,
    InMemoryDecisionRepository,
    InMemoryFeedbackRepository,
    InMemoryOutcomeRepository,
    InMemoryProactiveRuleRepository,
    InMemorySignalRepository,
)
from max.proactive.services.anti_spam import (
    AttentionBudgetService,
    CircuitBreakerService,
    ProactiveDeduplicationService,
)
from max.proactive.services.decision_engine import (
    ActionExecutionService,
    CandidateGenerator,
    FeedbackService,
    ProactiveDecisionEngine,
    SignalIngestionService,
)
from max.proactive.services.evaluators import (
    ConfidenceEvaluator,
    ImportanceEvaluator,
    RelevanceEvaluator,
    UrgencyEvaluator,
)
from max.proactive.services.policy_engine import ProactivePolicyEngine

logger = logging.getLogger(__name__)


class ProactiveContainer:
    """Dependency Injection container managing components of Module 30."""

    _instance: ProactiveContainer | None = None

    def __init__(self) -> None:
        self.settings = get_settings().proactive

        # Repositories
        self.signal_repo = InMemorySignalRepository()
        self.candidate_repo = InMemoryCandidateRepository()
        self.decision_repo = InMemoryDecisionRepository()
        self.action_repo = InMemoryActionRepository()
        self.outcome_repo = InMemoryOutcomeRepository()
        self.feedback_repo = InMemoryFeedbackRepository()
        self.rule_repo = InMemoryProactiveRuleRepository()
        self.audit_repo = InMemoryAuditRepository()

        # Adapters
        self.user_profile_adapter = UserProfileAdapter(
            mode=ProactiveMode(self.settings.mode.upper())
        )
        self.context_adapter = ContextMemoryKnowledgeAdapter()
        self.task_adapter = TaskIntegrationAdapter()
        self.permission_adapter = PermissionGateAdapter()
        self.notification_adapter = NotificationSystemAdapter()
        self.scheduler_adapter = SchedulerIntegrationAdapter()
        self.external_adapter = ExternalIntegrationAdapter()

        # Evaluators & Anti-Spam
        self.relevance_evaluator = RelevanceEvaluator(self.context_adapter)
        self.importance_evaluator = ImportanceEvaluator()
        self.urgency_evaluator = UrgencyEvaluator()
        self.confidence_evaluator = ConfidenceEvaluator()
        self.dedup_service = ProactiveDeduplicationService(
            self.candidate_repo, self.decision_repo, self.settings.default_cooldown_seconds
        )
        self.budget_service = AttentionBudgetService(self.settings)
        self.circuit_breaker = CircuitBreakerService()

        # Policy & Decision Services
        self.policy_engine = ProactivePolicyEngine(
            self.settings, self.user_profile_adapter, self.rule_repo
        )
        self.candidate_generator = CandidateGenerator()
        self.ingestion_service = SignalIngestionService(
            self.signal_repo, self.candidate_generator, self.audit_repo
        )
        self.action_execution_service = ActionExecutionService(
            self.permission_adapter,
            self.notification_adapter,
            self.task_adapter,
            self.scheduler_adapter,
            self.action_repo,
            self.outcome_repo,
            self.audit_repo,
            self.budget_service,
        )
        self.decision_engine = ProactiveDecisionEngine(
            self.settings,
            self.signal_repo,
            self.candidate_repo,
            self.decision_repo,
            self.rule_repo,
            self.audit_repo,
            self.relevance_evaluator,
            self.importance_evaluator,
            self.urgency_evaluator,
            self.confidence_evaluator,
            self.dedup_service,
            self.budget_service,
            self.circuit_breaker,
            self.policy_engine,
            self.action_execution_service,
            self.ingestion_service,
        )
        self.feedback_service = FeedbackService(self.feedback_repo, self.audit_repo)

    @classmethod
    def get_instance(cls) -> ProactiveContainer:
        """Get or create singleton instance of ProactiveContainer."""
        if cls._instance is None:
            cls._instance = ProactiveContainer()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (primarily for test isolation)."""
        cls._instance = None
