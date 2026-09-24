"""Proactive Policy Engine for Module 30 — Proactive Intelligence Engine."""

import logging

from max.config.sections import ProactiveSettings
from max.proactive.adapters.adapters import UserProfileAdapter
from max.proactive.domain.enums import (
    ActionType,
    AutonomyLevel,
    DecisionType,
    ImportanceLevel,
    ProactiveMode,
    RuleStatus,
    UrgencyLevel,
    UserState,
)
from max.proactive.domain.models import ProactiveCandidate, ProactiveDecision, ProactiveRule
from max.proactive.repositories.repositories import ProactiveRuleRepository

logger = logging.getLogger(__name__)


class ProactivePolicyEngine:
    """Evaluates candidate opportunities against policies, rules, user state, and autonomy levels."""

    def __init__(
        self,
        settings: ProactiveSettings,
        user_profile_adapter: UserProfileAdapter,
        rule_repository: ProactiveRuleRepository,
    ) -> None:
        self._settings = settings
        self._user_profile_adapter = user_profile_adapter
        self._rule_repo = rule_repository

    async def evaluate_candidate(
        self,
        candidate: ProactiveCandidate,
        owner_id: str = "default_owner",
    ) -> ProactiveDecision:
        """Evaluate a candidate against structured policies and rules."""
        current_mode = self._user_profile_adapter.get_proactive_mode(owner_id)
        user_state = self._user_profile_adapter.get_user_state(owner_id)

        # Step 1: Mode Check
        if current_mode == ProactiveMode.PASSIVE:
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.STAY_SILENT,
                reason="Proactive mode is set to PASSIVE (Observe only)",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_0,
            )

        # Step 2: Confidence & Relevance Threshold Check
        if candidate.confidence < self._settings.min_confidence:
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.STAY_SILENT,
                reason=f"Candidate confidence ({candidate.confidence:.2f}) below threshold ({self._settings.min_confidence:.2f})",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_0,
            )

        if candidate.relevance < self._settings.min_relevance:
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.STAY_SILENT,
                reason=f"Candidate relevance ({candidate.relevance:.2f}) below threshold ({self._settings.min_relevance:.2f})",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_0,
            )

        # Step 3: Quiet Hours / User State Check
        is_quiet = self._user_profile_adapter.is_quiet_hours(owner_id)
        if is_quiet and candidate.importance != ImportanceLevel.CRITICAL and candidate.urgency != UrgencyLevel.CRITICAL:
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.STAY_SILENT,
                reason=f"User is currently in quiet/focus state ({user_state}) and event is not CRITICAL",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_0,
            )

        # Step 4: Custom Structured Rules Evaluation
        active_rules = await self._rule_repo.list_rules(owner_id)
        for rule in active_rules:
            if rule.status != RuleStatus.ACTIVE:
                continue
            if self._matches_rule(candidate, user_state, rule):
                autonomy = self._resolve_autonomy_for_decision(rule.decision_type)
                return ProactiveDecision(
                    candidate_id=candidate.candidate_id,
                    owner_id=owner_id,
                    decision_type=rule.decision_type,
                    reason=f"Matched custom proactive rule: {rule.name}",
                    confidence=candidate.confidence,
                    autonomy_level=autonomy,
                    proposed_action={
                        "action_type": rule.decision_type.value,
                        "rule_id": rule.rule_id,
                    },
                )

        # Step 5: Default Heuristic Decision Matrix
        default_autonomy = AutonomyLevel(self._settings.default_autonomy_level)

        if candidate.importance == ImportanceLevel.CRITICAL or candidate.urgency == UrgencyLevel.CRITICAL:
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.NOTIFY,
                reason="High importance/urgency critical event requiring immediate user notification",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_1,
                proposed_action={"action_type": ActionType.NOTIFY.value},
            )

        if candidate.importance == ImportanceLevel.HIGH:
            if default_autonomy >= AutonomyLevel.LEVEL_3 and candidate.actionability:
                return ProactiveDecision(
                    candidate_id=candidate.candidate_id,
                    owner_id=owner_id,
                    decision_type=DecisionType.CREATE_TASK,
                    reason="High importance actionable event; creating proactive task",
                    confidence=candidate.confidence,
                    autonomy_level=AutonomyLevel.LEVEL_3,
                    proposed_action={"action_type": ActionType.CREATE_TASK.value},
                )
            return ProactiveDecision(
                candidate_id=candidate.candidate_id,
                owner_id=owner_id,
                decision_type=DecisionType.NOTIFY,
                reason="High importance event; notifying user",
                confidence=candidate.confidence,
                autonomy_level=AutonomyLevel.LEVEL_1,
                proposed_action={"action_type": ActionType.NOTIFY.value},
            )

        if candidate.importance == ImportanceLevel.MEDIUM:
            if user_state in (UserState.AVAILABLE, UserState.FOCUSED):
                return ProactiveDecision(
                    candidate_id=candidate.candidate_id,
                    owner_id=owner_id,
                    decision_type=DecisionType.RECOMMEND,
                    reason="Medium importance event; proposing recommendation while user is available",
                    confidence=candidate.confidence,
                    autonomy_level=AutonomyLevel.LEVEL_2,
                    proposed_action={"action_type": ActionType.RECOMMEND.value},
                )

        return ProactiveDecision(
            candidate_id=candidate.candidate_id,
            owner_id=owner_id,
            decision_type=DecisionType.STAY_SILENT,
            reason="Low importance/urgency candidate; remaining silent to conserve user attention",
            confidence=candidate.confidence,
            autonomy_level=AutonomyLevel.LEVEL_0,
        )

    def _matches_rule(
        self, candidate: ProactiveCandidate, user_state: UserState, rule: ProactiveRule
    ) -> bool:
        if rule.candidate_type and rule.candidate_type != candidate.candidate_type:
            return False
        if user_state not in rule.allowed_user_states:
            return False
        if candidate.confidence < rule.min_confidence:
            return False
        if candidate.relevance < rule.min_relevance:
            return False

        # Compare importance & urgency levels
        importance_order = [
            ImportanceLevel.LOW,
            ImportanceLevel.MEDIUM,
            ImportanceLevel.HIGH,
            ImportanceLevel.CRITICAL,
        ]
        if importance_order.index(candidate.importance) < importance_order.index(rule.min_importance):
            return False

        urgency_order = [
            UrgencyLevel.LOW,
            UrgencyLevel.MEDIUM,
            UrgencyLevel.HIGH,
            UrgencyLevel.CRITICAL,
        ]
        if urgency_order.index(candidate.urgency) < urgency_order.index(rule.min_urgency):
            return False

        return True

    def _resolve_autonomy_for_decision(self, decision_type: DecisionType) -> AutonomyLevel:
        mapping = {
            DecisionType.STAY_SILENT: AutonomyLevel.LEVEL_0,
            DecisionType.NOTIFY: AutonomyLevel.LEVEL_1,
            DecisionType.RECOMMEND: AutonomyLevel.LEVEL_2,
            DecisionType.ASK_USER: AutonomyLevel.LEVEL_2,
            DecisionType.CREATE_TASK: AutonomyLevel.LEVEL_3,
            DecisionType.TRIGGER_AUTOMATION: AutonomyLevel.LEVEL_4,
            DecisionType.EXECUTE_ACTION: AutonomyLevel.LEVEL_4,
        }
        return mapping.get(decision_type, AutonomyLevel.LEVEL_1)
