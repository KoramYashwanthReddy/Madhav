"""Master Proactive Decision Engine and Orchestrator for Module 30."""

import logging
from datetime import UTC, datetime

from max.config.sections import ProactiveSettings
from max.proactive.adapters.adapters import (
    NotificationSystemAdapter,
    PermissionGateAdapter,
    SchedulerIntegrationAdapter,
    TaskIntegrationAdapter,
)
from max.proactive.domain.enums import (
    ActionStatus,
    ActionType,
    AutonomyLevel,
    DecisionType,
    ImportanceLevel,
    UrgencyLevel,
)
from max.proactive.domain.models import (
    ProactiveAction,
    ProactiveCandidate,
    ProactiveDecision,
    ProactiveFeedback,
    ProactiveOutcome,
    ProactiveSignal,
    ProactiveSimulationResult,
)
from max.proactive.repositories.repositories import (
    ActionRepository,
    AuditRepository,
    CandidateRepository,
    DecisionRepository,
    FeedbackRepository,
    OutcomeRepository,
    ProactiveRuleRepository,
    SignalRepository,
)
from max.proactive.services.anti_spam import (
    AttentionBudgetService,
    CircuitBreakerService,
    ProactiveDeduplicationService,
)
from max.proactive.services.evaluators import (
    ConfidenceEvaluator,
    ImportanceEvaluator,
    RelevanceEvaluator,
    UrgencyEvaluator,
)
from max.proactive.services.policy_engine import ProactivePolicyEngine

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class CandidateGenerator:
    """Generates proactive candidates from normalized signals."""

    def generate_candidates(self, signal: ProactiveSignal) -> list[ProactiveCandidate]:
        """Convert a signal into 0, 1, or multiple candidate opportunities."""
        candidates: list[ProactiveCandidate] = []

        # Prompt injection safety check: check for explicit malicious instruction payload
        payload_text = str(signal.payload_reference).lower()
        if "ignore all max rules" in payload_text or "attacker.example" in payload_text:
            logger.warning("Potential prompt injection detected in signal %s; creating benign security candidate", signal.signal_id)
            cand = ProactiveCandidate(
                owner_id=signal.owner_id,
                signal_id=signal.signal_id,
                candidate_type="security.malicious_signal_detected",
                description="Potential malicious prompt injection signal ignored and logged for security audit.",
                importance=ImportanceLevel.CRITICAL,
                urgency=UrgencyLevel.HIGH,
                confidence=0.99,
                relevance=1.0,
                actionability=False,
                sensitivity="HIGH",
                category="SECURITY",
                deduplication_key=f"{signal.owner_id}:security:malicious_signal",
            )
            return [cand]

        dedup_key = signal.deduplication_key or f"{signal.owner_id}:{signal.source}:{signal.signal_type}"

        cand = ProactiveCandidate(
            owner_id=signal.owner_id,
            signal_id=signal.signal_id,
            candidate_type=signal.signal_type,
            description=f"Proactive candidate from {signal.source} event '{signal.signal_type}'",
            importance=signal.importance_hint,
            urgency=UrgencyLevel.MEDIUM,
            confidence=0.75,
            relevance=0.70,
            actionability=True,
            category=signal.source.value,
            deduplication_key=dedup_key,
        )
        candidates.append(cand)
        return candidates


class SignalIngestionService:
    """Ingests, validates, normalizes, and classifies raw signals."""

    def __init__(
        self,
        signal_repo: SignalRepository,
        candidate_generator: CandidateGenerator,
        audit_repo: AuditRepository,
    ) -> None:
        self._signal_repo = signal_repo
        self._candidate_generator = candidate_generator
        self._audit_repo = audit_repo

    async def ingest_signal(self, signal: ProactiveSignal) -> tuple[ProactiveSignal, list[ProactiveCandidate]]:
        """Ingest signal, store safely, and produce candidates."""
        await self._signal_repo.save_signal(signal)
        await self._audit_repo.record_event(
            owner_id=signal.owner_id,
            event_type="SIGNAL_INGESTED",
            details={"signal_id": signal.signal_id, "source": signal.source, "type": signal.signal_type},
        )
        candidates = self._candidate_generator.generate_candidates(signal)
        return signal, candidates


class ActionExecutionService:
    """Executes or requests permissions for actions derived from decisions."""

    def __init__(
        self,
        permission_adapter: PermissionGateAdapter,
        notification_adapter: NotificationSystemAdapter,
        task_adapter: TaskIntegrationAdapter,
        scheduler_adapter: SchedulerIntegrationAdapter,
        action_repo: ActionRepository,
        outcome_repo: OutcomeRepository,
        audit_repo: AuditRepository,
        budget_service: AttentionBudgetService,
    ) -> None:
        self._permission_adapter = permission_adapter
        self._notification_adapter = notification_adapter
        self._task_adapter = task_adapter
        self._scheduler_adapter = scheduler_adapter
        self._action_repo = action_repo
        self._outcome_repo = outcome_repo
        self._audit_repo = audit_repo
        self._budget_service = budget_service

    async def execute_decision_action(
        self,
        decision: ProactiveDecision,
        candidate: ProactiveCandidate,
        owner_id: str = "default_owner",
    ) -> ProactiveAction | None:
        """Process decision output and execute authorized action or create approval request."""
        if decision.decision_type == DecisionType.STAY_SILENT:
            return None

        # Build ProactiveAction entity
        action_type = ActionType(decision.decision_type.value)
        action = ProactiveAction(
            decision_id=decision.decision_id,
            owner_id=owner_id,
            action_type=action_type,
            target=candidate.category,
            arguments={"candidate_id": candidate.candidate_id, "description": candidate.description},
            risk_level="HIGH" if decision.decision_type == DecisionType.EXECUTE_ACTION else "LOW",
            status=ActionStatus.PENDING,
        )

        if decision.decision_type == DecisionType.NOTIFY:
            # Check attention budget
            allowed, reason = self._budget_service.can_consume_budget(owner_id)
            if not allowed:
                logger.info("Attention budget reached for %s; notification suppressed", owner_id)
                action.status = ActionStatus.CANCELLED
                await self._action_repo.save_action(action)
                return action

            self._budget_service.consume_budget(owner_id)
            notif_res = await self._notification_adapter.send_proactive_notification(
                title=f"MAX Proactive: {candidate.candidate_type}",
                body=candidate.description,
                recipient_id=owner_id,
                importance=candidate.importance,
                urgency=candidate.urgency,
            )
            action.status = ActionStatus.EXECUTED
            action.metadata["notification"] = notif_res

        elif decision.decision_type == DecisionType.CREATE_TASK:
            task_res = await self._task_adapter.create_proactive_task(
                candidate=candidate, owner_id=owner_id
            )
            action.status = ActionStatus.EXECUTED
            action.metadata["task"] = task_res

        elif decision.decision_type == DecisionType.TRIGGER_AUTOMATION:
            trig_res = await self._scheduler_adapter.trigger_automation(
                automation_name=candidate.candidate_type, owner_id=owner_id
            )
            action.status = ActionStatus.EXECUTED
            action.metadata["automation"] = trig_res

        elif decision.decision_type in (DecisionType.EXECUTE_ACTION, DecisionType.RECOMMEND, DecisionType.ASK_USER):
            # Check Module 15 permission gate
            allowed, require_approval, reason = await self._permission_adapter.check_permission(
                action=action, owner_id=owner_id
            )
            if allowed and decision.autonomy_level >= AutonomyLevel.LEVEL_4:
                action.status = ActionStatus.EXECUTED
                action.metadata["execution_reason"] = reason
            elif require_approval:
                action.status = ActionStatus.PENDING_APPROVAL
                action.metadata["approval_reason"] = reason
                # Send approval request notification via Module 27
                await self._notification_adapter.send_proactive_notification(
                    title="MAX Approval Required",
                    body=f"Action requires explicit user approval: {candidate.description}",
                    recipient_id=owner_id,
                    importance=ImportanceLevel.HIGH,
                )
            else:
                action.status = ActionStatus.REJECTED
                action.metadata["rejection_reason"] = reason

        await self._action_repo.save_action(action)
        await self._audit_repo.record_event(
            owner_id=owner_id,
            event_type="ACTION_PROPOSED",
            details={"action_id": action.action_id, "type": action.action_type, "status": action.status},
        )

        outcome = ProactiveOutcome(
            action_id=action.action_id,
            owner_id=owner_id,
            status=action.status,
            result=action.metadata,
        )
        await self._outcome_repo.save_outcome(outcome)

        return action


class ProactiveDecisionEngine:
    """Master Decision Engine combining ingestion, evaluation, policy checks, and execution."""

    def __init__(
        self,
        settings: ProactiveSettings,
        signal_repo: SignalRepository,
        candidate_repo: CandidateRepository,
        decision_repo: DecisionRepository,
        rule_repo: ProactiveRuleRepository,
        audit_repo: AuditRepository,
        relevance_evaluator: RelevanceEvaluator,
        importance_evaluator: ImportanceEvaluator,
        urgency_evaluator: UrgencyEvaluator,
        confidence_evaluator: ConfidenceEvaluator,
        dedup_service: ProactiveDeduplicationService,
        budget_service: AttentionBudgetService,
        circuit_breaker: CircuitBreakerService,
        policy_engine: ProactivePolicyEngine,
        action_execution_service: ActionExecutionService,
        ingestion_service: SignalIngestionService,
    ) -> None:
        self._settings = settings
        self._signal_repo = signal_repo
        self._candidate_repo = candidate_repo
        self._decision_repo = decision_repo
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo
        self._relevance_eval = relevance_evaluator
        self._importance_eval = importance_evaluator
        self._urgency_eval = urgency_evaluator
        self._confidence_eval = confidence_evaluator
        self._dedup_service = dedup_service
        self._budget_service = budget_service
        self._circuit_breaker = circuit_breaker
        self._policy_engine = policy_engine
        self._action_execution_service = action_execution_service
        self._ingestion_service = ingestion_service

    async def process_signal(
        self, signal: ProactiveSignal
    ) -> list[tuple[ProactiveCandidate, ProactiveDecision, ProactiveAction | None]]:
        """Run complete proactive pipeline for an incoming signal."""
        ingested_sig, candidates = await self._ingestion_service.ingest_signal(signal)
        results: list[tuple[ProactiveCandidate, ProactiveDecision, ProactiveAction | None]] = []

        for candidate in candidates:
            # 1. Multi-dimensional evaluation
            candidate.importance = self._importance_eval.evaluate(
                ingested_sig, candidate.candidate_type, candidate.metadata
            )
            candidate.urgency = self._urgency_eval.evaluate(
                ingested_sig, candidate.candidate_type, candidate.metadata
            )
            candidate.confidence = self._confidence_eval.evaluate(
                ingested_sig, candidate.candidate_type
            )
            rel_score, rel_reason = self._relevance_eval.evaluate(candidate, candidate.owner_id)
            candidate.relevance = rel_score

            # Save candidate
            await self._candidate_repo.save_candidate(candidate)

            # 2. Check Deduplication
            is_dup, dup_reason = await self._dedup_service.is_duplicate_candidate(candidate)
            if is_dup:
                decision = ProactiveDecision(
                    candidate_id=candidate.candidate_id,
                    owner_id=candidate.owner_id,
                    decision_type=DecisionType.STAY_SILENT,
                    reason=f"Deduplicated: {dup_reason}",
                    confidence=candidate.confidence,
                    autonomy_level=AutonomyLevel.LEVEL_0,
                )
                await self._decision_repo.save_decision(decision)
                results.append((candidate, decision, None))
                continue

            # 3. Policy Evaluation
            decision = await self._policy_engine.evaluate_candidate(candidate, candidate.owner_id)

            # Save decision
            await self._decision_repo.save_decision(decision)
            await self._audit_repo.record_event(
                owner_id=candidate.owner_id,
                event_type="DECISION_MADE",
                details={
                    "decision_id": decision.decision_id,
                    "candidate_id": candidate.candidate_id,
                    "type": decision.decision_type,
                    "reason": decision.reason,
                },
            )

            # 4. Action Execution
            action = await self._action_execution_service.execute_decision_action(
                decision=decision, candidate=candidate, owner_id=candidate.owner_id
            )

            results.append((candidate, decision, action))

        return results

    async def simulate_signal(self, signal: ProactiveSignal) -> ProactiveSimulationResult:
        """Simulate proactive evaluation pipeline deterministically without side effects."""
        candidates = CandidateGenerator().generate_candidates(signal)

        if not candidates:
            cand = ProactiveCandidate(
                owner_id=signal.owner_id,
                signal_id=signal.signal_id,
                candidate_type=signal.signal_type,
                description="Simulated candidate",
            )
            candidates = [cand]

        candidate = candidates[0]
        candidate.importance = self._importance_eval.evaluate(signal, candidate.candidate_type, {})
        candidate.urgency = self._urgency_eval.evaluate(signal, candidate.candidate_type, {})
        candidate.confidence = self._confidence_eval.evaluate(signal, candidate.candidate_type)
        rel_score, _ = self._relevance_eval.evaluate(candidate, candidate.owner_id)
        candidate.relevance = rel_score

        decision = await self._policy_engine.evaluate_candidate(candidate, candidate.owner_id)

        action = None
        if decision.decision_type != DecisionType.STAY_SILENT:
            action = ProactiveAction(
                decision_id=decision.decision_id,
                owner_id=signal.owner_id,
                action_type=ActionType(decision.decision_type.value),
                target="SIMULATED_TARGET",
                status=ActionStatus.PENDING,
            )

        return ProactiveSimulationResult(
            signal=signal,
            candidates=candidates,
            decision=decision,
            proposed_action=action,
        )


class FeedbackService:
    """Collects explicit user feedback on proactive decisions."""

    def __init__(self, feedback_repo: FeedbackRepository, audit_repo: AuditRepository) -> None:
        self._feedback_repo = feedback_repo
        self._audit_repo = audit_repo

    async def record_feedback(self, feedback: ProactiveFeedback) -> ProactiveFeedback:
        saved = await self._feedback_repo.save_feedback(feedback)
        await self._audit_repo.record_event(
            owner_id=feedback.owner_id,
            event_type="FEEDBACK_RECORDED",
            details={
                "feedback_id": feedback.feedback_id,
                "decision_id": feedback.decision_id,
                "type": feedback.feedback_type,
            },
        )
        return saved
