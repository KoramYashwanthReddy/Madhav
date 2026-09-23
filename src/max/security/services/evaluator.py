"""Deterministic policy evaluation engine for Module 15 — Permission & Security."""

from typing import Any

from max.security.domain.decision import PermissionDecision, SecurityContext
from max.security.domain.enums import (
    DecisionReason,
    PermissionDecisionStatus,
    PermissionEffect,
    RiskLevel,
    SecurityMode,
)
from max.security.domain.grant import PermissionGrant
from max.security.domain.permission import PermissionCondition, PermissionRule
from max.security.repositories.permission_repository import BasePermissionGrantRepository
from max.security.repositories.policy_repository import BasePolicyRepository
from max.security.utils.domain_url import is_domain_allowed
from max.security.utils.path import is_path_under_root


class PermissionEvaluator:
    """Deterministic policy evaluation engine enforcing security precedence rules."""

    def __init__(
        self,
        policy_repository: BasePolicyRepository,
        grant_repository: BasePermissionGrantRepository | None = None,
    ) -> None:
        self._policy_repo = policy_repository
        self._grant_repo = grant_repository

    def evaluate(
        self,
        context: SecurityContext,
        request_id: str,
    ) -> PermissionDecision:
        """Evaluate security context against policies and return deterministic PermissionDecision.

        Precedence Rules:
        1. Emergency DENY (Kill switch active) -> BLOCKED, EMERGENCY_BLOCK
        2. Security mode DENY (LOCKDOWN mode blocks HIGH/CRITICAL actions) -> BLOCKED, SECURITY_MODE_BLOCKED
        3. Owner boundary DENY (Subject/Resource owner mismatch) -> DENIED, OWNER_MISMATCH
        4. Active Permission Grant match -> ALLOW / REQUIRES_APPROVAL
        5. Active Policy Rules evaluation -> EXPLICIT_DENY, EXPLICIT_ALLOW, APPROVAL_REQUIRED
        6. Default DENY -> DENIED, NO_POLICY_MATCH
        7. Fail Closed on error -> ERROR, EVALUATION_ERROR
        """
        try:
            # 1. Emergency Block Check
            if context.emergency_block_active:
                return PermissionDecision(
                    request_id=request_id,
                    status=PermissionDecisionStatus.BLOCKED,
                    effect=PermissionEffect.DENY,
                    reason=DecisionReason.EMERGENCY_BLOCK,
                    message="Global emergency block is active. Action blocked.",
                    policy_version=context.policy_version,
                )

            # 2. Security Mode Check
            if context.security_mode == SecurityMode.LOCKDOWN:
                if context.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
                    return PermissionDecision(
                        request_id=request_id,
                        status=PermissionDecisionStatus.BLOCKED,
                        effect=PermissionEffect.DENY,
                        reason=DecisionReason.SECURITY_MODE_BLOCKED,
                        message="System in LOCKDOWN security mode. High and Critical risk actions are blocked.",
                        policy_version=context.policy_version,
                    )
            elif context.security_mode == SecurityMode.MAINTENANCE:
                return PermissionDecision(
                    request_id=request_id,
                    status=PermissionDecisionStatus.BLOCKED,
                    effect=PermissionEffect.DENY,
                    reason=DecisionReason.SECURITY_MODE_BLOCKED,
                    message="System in MAINTENANCE security mode. External operations are disabled.",
                    policy_version=context.policy_version,
                )

            # 3. Owner Boundary Check
            if context.resource.owner_id and context.principal.owner_id:
                if context.resource.owner_id != context.principal.owner_id:
                    return PermissionDecision(
                        request_id=request_id,
                        status=PermissionDecisionStatus.DENIED,
                        effect=PermissionEffect.DENY,
                        reason=DecisionReason.OWNER_MISMATCH,
                        message=f"Cross-owner access denied. Resource owner '{context.resource.owner_id}' does not match principal owner '{context.principal.owner_id}'.",
                        policy_version=context.policy_version,
                    )

            # 4. Check Permission Grants
            if self._grant_repo:
                grants, _ = self._grant_repo.list_grants(
                    owner_id=context.owner_id,
                    subject_id=context.principal.subject.subject_id,
                    active_only=True,
                )
                for grant in grants:
                    if self._grant_matches_context(grant, context):
                        if grant.grant_type == "ONE_TIME":
                            # Mark grant as used
                            self._grant_repo.save(
                                grant.model_copy(update={"used_count": grant.used_count + 1})
                            )
                        return PermissionDecision(
                            request_id=request_id,
                            status=PermissionDecisionStatus.ALLOWED,
                            effect=PermissionEffect.ALLOW,
                            reason=DecisionReason.EXPLICIT_ALLOW,
                            message=f"Permission granted by explicit grant '{grant.grant_id}'.",
                            policy_version=context.policy_version,
                        )

            # 5. Evaluate Policies
            policies, _ = self._policy_repo.list_policies(
                owner_id=context.owner_id,
                enabled_only=True,
            )

            # Sort policies by priority descending
            policies.sort(key=lambda p: p.priority, reverse=True)

            for policy in policies:
                rules = sorted(policy.rules, key=lambda r: r.priority, reverse=True)
                for rule in rules:
                    if self._rule_matches_context(rule, context):
                        if rule.effect == PermissionEffect.DENY:
                            return PermissionDecision(
                                request_id=request_id,
                                status=PermissionDecisionStatus.DENIED,
                                effect=PermissionEffect.DENY,
                                reason=DecisionReason.EXPLICIT_DENY,
                                message=f"Explicitly denied by policy '{policy.name}' (rule '{rule.rule_id}'): {rule.reason}",
                                policy_id=policy.policy_id,
                                rule_id=rule.rule_id,
                                policy_version=context.policy_version,
                            )
                        elif rule.effect == PermissionEffect.REQUIRE_APPROVAL:
                            return PermissionDecision(
                                request_id=request_id,
                                status=PermissionDecisionStatus.REQUIRES_APPROVAL,
                                effect=PermissionEffect.REQUIRE_APPROVAL,
                                reason=DecisionReason.APPROVAL_REQUIRED,
                                message=f"Approval required by policy '{policy.name}' (rule '{rule.rule_id}'): {rule.reason}",
                                policy_id=policy.policy_id,
                                rule_id=rule.rule_id,
                                approval_required=True,
                                policy_version=context.policy_version,
                            )
                        elif rule.effect == PermissionEffect.ALLOW:
                            # If security mode RESTRICTED requires approval for HIGH/CRITICAL
                            if (
                                context.security_mode == SecurityMode.RESTRICTED
                                and context.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
                            ):
                                return PermissionDecision(
                                    request_id=request_id,
                                    status=PermissionDecisionStatus.REQUIRES_APPROVAL,
                                    effect=PermissionEffect.REQUIRE_APPROVAL,
                                    reason=DecisionReason.APPROVAL_REQUIRED,
                                    message="RESTRICTED security mode requires approval for High/Critical risk actions.",
                                    policy_id=policy.policy_id,
                                    rule_id=rule.rule_id,
                                    approval_required=True,
                                    policy_version=context.policy_version,
                                )

                            return PermissionDecision(
                                request_id=request_id,
                                status=PermissionDecisionStatus.ALLOWED,
                                effect=PermissionEffect.ALLOW,
                                reason=DecisionReason.EXPLICIT_ALLOW,
                                message=f"Allowed by policy '{policy.name}' (rule '{rule.rule_id}').",
                                policy_id=policy.policy_id,
                                rule_id=rule.rule_id,
                                policy_version=context.policy_version,
                            )

            # 6. Default Deny
            return PermissionDecision(
                request_id=request_id,
                status=PermissionDecisionStatus.DENIED,
                effect=PermissionEffect.DENY,
                reason=DecisionReason.NO_POLICY_MATCH,
                message="Default deny: No matching policy rule explicitly allowed this action.",
                policy_version=context.policy_version,
            )

        except Exception as err:
            # 7. Fail Closed
            return PermissionDecision(
                request_id=request_id,
                status=PermissionDecisionStatus.ERROR,
                effect=PermissionEffect.DENY,
                reason=DecisionReason.EVALUATION_ERROR,
                message=f"Fail-closed: Evaluation failed with error: {str(err)}",
                policy_version=context.policy_version,
            )

    def _grant_matches_context(self, grant: PermissionGrant, context: SecurityContext) -> bool:
        if grant.subject.subject_id != context.principal.subject.subject_id:
            return False
        if grant.action != context.action:
            return False
        if grant.resource.resource_type != context.resource.resource_type:
            return False

        if grant.scope == "EXACT_RESOURCE":
            return grant.resource.resource_id == context.resource.resource_id
        elif grant.scope == "DIRECTORY":
            return is_path_under_root(
                context.resource.location or context.resource.resource_id,
                grant.resource.location or grant.resource.resource_id,
            )
        elif grant.scope == "GLOBAL":
            return True

        return grant.resource.resource_id == context.resource.resource_id

    def _rule_matches_context(self, rule: PermissionRule, context: SecurityContext) -> bool:
        if not self._eval_conditions(rule.subject_conditions, context, category="subject"):
            return False
        if not self._eval_conditions(rule.action_conditions, context, category="action"):
            return False
        if not self._eval_conditions(rule.resource_conditions, context, category="resource"):
            return False
        if not self._eval_conditions(rule.tool_conditions, context, category="tool"):
            return False
        if not self._eval_conditions(rule.time_conditions, context, category="time"):
            return False
        return True

    def _eval_conditions(
        self, conditions: list[PermissionCondition], context: SecurityContext, category: str
    ) -> bool:
        for cond in conditions:
            actual_val = self._resolve_condition_value(cond.field, context)
            if not self._match_condition(cond.operator, actual_val, cond.value):
                return False
        return True

    def _resolve_condition_value(self, field: str, context: SecurityContext) -> Any:
        field_path = field.lower().split(".")
        if field_path[0] == "subject":
            if len(field_path) > 1:
                if field_path[1] == "subject_type":
                    return context.principal.subject.subject_type.value
                elif field_path[1] == "subject_id":
                    return context.principal.subject.subject_id
            return context.principal.subject.subject_id
        elif field_path[0] == "action":
            return context.action.value
        elif field_path[0] == "resource":
            if len(field_path) > 1:
                if field_path[1] == "resource_type":
                    return context.resource.resource_type
                elif field_path[1] == "resource_id":
                    return context.resource.resource_id
                elif field_path[1] == "location":
                    return context.resource.location or context.resource.resource_id
            return context.resource.resource_id
        elif field_path[0] == "tool":
            return context.tool_id or ""
        elif field_path[0] == "risk_level":
            return context.risk_level.value

        return None

    def _match_condition(self, operator: str, actual: Any, expected: Any) -> bool:
        op = operator.upper()
        if op == "EQUALS":
            return str(actual) == str(expected)
        elif op == "NOT_EQUALS":
            return str(actual) != str(expected)
        elif op == "IN":
            if isinstance(expected, list):
                return str(actual) in [str(x) for x in expected]
            return str(actual) in str(expected)
        elif op == "CONTAINS":
            return str(expected) in str(actual)
        elif op == "STARTS_WITH":
            return str(actual).startswith(str(expected))
        elif op == "MATCHES_PATH":
            return is_path_under_root(str(actual), str(expected))
        elif op == "MATCHES_DOMAIN":
            return is_domain_allowed(str(actual), str(expected))
        return False
