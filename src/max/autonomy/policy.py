"""Autonomy Governance Policy and Risk Assessment Engine."""

import fnmatch
import logging
from typing import Any

from max.autonomy.domain import (
    ApprovalRequest,
    ApprovalStatus,
    AutonomyLevel,
    AutonomyPolicy,
    Mission,
    RiskLevel,
)
from max.config.settings import Settings, get_settings
from max.security.container import get_security_container

logger = logging.getLogger(__name__)


class AutonomyRiskService:
    """Classifies risk levels for proposed autonomous steps based on target resource, reversibility, and impact."""

    def __init__(self) -> None:
        self.critical_patterns = [
            "*delete*",
            "*purge*",
            "*remove*",
            "*format*",
            "*credential*",
            "*password*",
            "*token*",
            "*key*",
            "*financial*",
            "*pay*",
            "*billing*",
            "*permission*",
            "*security*",
            "*grant*",
            "*deploy*",
            "*shutdown*",
        ]
        self.high_patterns = [
            "*write*",
            "*modify*",
            "*update*",
            "*post*",
            "*send_email*",
            "*publish*",
            "*execute_command*",
            "*install*",
        ]
        self.medium_patterns = [
            "*create_draft*",
            "*notify*",
            "*task_create*",
            "*append*",
        ]

    def classify_risk(self, action_name: str, target_resource: str = "", arguments: dict[str, Any] | None = None) -> RiskLevel:
        """Evaluate action name and target parameters against risk rules."""
        combined_str = f"{action_name} {target_resource} {str(arguments or {})}".lower()

        for pattern in self.critical_patterns:
            if fnmatch.fnmatch(combined_str, pattern):
                return RiskLevel.CRITICAL

        for pattern in self.high_patterns:
            if fnmatch.fnmatch(combined_str, pattern):
                return RiskLevel.HIGH

        for pattern in self.medium_patterns:
            if fnmatch.fnmatch(combined_str, pattern):
                return RiskLevel.MEDIUM

        return RiskLevel.LOW


class AutonomyPolicyService:
    """Enforces the mandatory 10-tier Autonomy Policy Hierarchy and Module 15 security integration."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.risk_service = AutonomyRiskService()
        self._policy = AutonomyPolicy()
        self._global_kill_switch: bool = False

    @property
    def policy(self) -> AutonomyPolicy:
        """Get active global autonomy policy."""
        return self._policy

    def update_policy(self, updates: dict[str, Any]) -> AutonomyPolicy:
        """Update active governance policy settings."""
        if "level" in updates and isinstance(updates["level"], str):
            updates["level"] = AutonomyLevel(updates["level"])
        if "require_approval_risk" in updates and isinstance(updates["require_approval_risk"], str):
            updates["require_approval_risk"] = RiskLevel(updates["require_approval_risk"])

        current = self._policy.model_dump()
        current.update(updates)
        self._policy = AutonomyPolicy(**current)
        logger.info("Updated global autonomy policy. Level set to %s.", self._policy.level.value)
        return self._policy

    def set_kill_switch(self, active: bool) -> bool:
        """Activate or deactivate the global emergency autonomy kill-switch."""
        self._global_kill_switch = active
        logger.warning("Global autonomy kill-switch state updated: active=%s", active)
        return self._global_kill_switch

    def is_kill_switch_active(self) -> bool:
        """Return kill switch status."""
        return self._global_kill_switch

    def evaluate_action_authorization(
        self,
        mission: Mission,
        action_name: str,
        target_resource: str = "",
        arguments: dict[str, Any] | None = None,
        pending_approval: ApprovalRequest | None = None,
    ) -> tuple[bool, str, RiskLevel]:
        """Enforces mandatory 10-tier policy hierarchy:
        1. Emergency DENY (Kill switch active)
        2. Module 15 Security DENY
        3. Explicit user DENY (blocked_actions pattern)
        4. System safety policy (CRITICAL actions require explicit approval)
        5. Resource limit / Budget check
        6. Mission scope check
        7. Tool policy check
        8. Approval requirement check (if risk >= threshold or pending approval unresolved)
        9. Explicit ALLOW
        10. Default DENY
        """
        args = arguments or {}
        risk = self.risk_service.classify_risk(action_name, target_resource, args)

        # 1. Emergency DENY (Kill-switch)
        if self._global_kill_switch:
            return False, "DENY: Global autonomy kill-switch is ACTIVE.", risk

        # 2. Module 15 Security Integration Check
        sec_container = get_security_container()
        if hasattr(sec_container, "evaluator"):
            sec_eval = sec_container.evaluator
            if hasattr(sec_eval, "is_action_allowed"):
                allowed_sec = sec_eval.is_action_allowed(
                    user_id=mission.owner_id, action=action_name, resource=target_resource
                )
                if not allowed_sec:
                    return False, f"DENY: Module 15 Security Engine explicitly blocked action '{action_name}'.", risk

        # 3. Explicit User DENY
        action_lower = action_name.lower()
        for blocked in self._policy.blocked_actions:
            if fnmatch.fnmatch(action_lower, blocked.lower()):
                return False, f"DENY: Action '{action_name}' matches blocked action pattern '{blocked}'.", risk

        # 4. System Safety Policy (Level 0 MANUAL mode or CRITICAL risk without explicit approval)
        if self._policy.level == AutonomyLevel.MANUAL:
            return False, "DENY: Autonomy level is set to Level 0 MANUAL. No autonomous actions permitted.", risk

        if risk == RiskLevel.CRITICAL and (not pending_approval or pending_approval.status != ApprovalStatus.APPROVED):
            return False, f"DENY: Action '{action_name}' is CRITICAL risk and requires explicit human approval.", risk

        # 5. Resource Limit / Budget Check
        if mission.used_budget["tool_calls"] >= mission.budget.max_tool_calls:
            return False, f"DENY: Mission tool call budget exceeded ({mission.used_budget['tool_calls']}/{mission.budget.max_tool_calls}).", risk

        # 6. Mission Scope Check
        if target_resource and mission.allowed_scope:
            in_scope = any(fnmatch.fnmatch(target_resource, scope) for scope in mission.allowed_scope)
            if not in_scope and not fnmatch.fnmatch(target_resource, "artifacts/*"):
                return False, f"DENY: Target resource '{target_resource}' escapes mission scope {mission.allowed_scope}.", risk

        # 7. Tool Policy Check (Assisted mode requirement)
        if self._policy.level == AutonomyLevel.ASSISTED and (not pending_approval or pending_approval.status != ApprovalStatus.APPROVED):
            return False, "DENY: Level 1 ASSISTED mode requires explicit human confirmation for all actions.", risk

        # 8. Approval Requirement Check
        risk_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        req_rank = risk_rank.get(self._policy.require_approval_risk.value, 3)
        act_rank = risk_rank.get(risk.value, 1)

        if act_rank >= req_rank:
            if not pending_approval or pending_approval.status != ApprovalStatus.APPROVED:
                return False, f"REQUIRES_APPROVAL: Action risk '{risk.value}' requires human approval.", risk

        # 9. Explicit ALLOW
        for allowed in self._policy.allowed_actions:
            if fnmatch.fnmatch(action_lower, allowed.lower()):
                return True, f"ALLOW: Action '{action_name}' matches allowed pattern '{allowed}'.", risk

        # 10. Default ALLOW for LOW/MEDIUM risk under Supervised/Delegated/Proactive/High Autonomy
        if act_rank < req_rank and self._policy.level in (
            AutonomyLevel.SUPERVISED,
            AutonomyLevel.DELEGATED,
            AutonomyLevel.PROACTIVE,
            AutonomyLevel.HIGH_AUTONOMY,
        ):
            return True, f"ALLOW: Bounded step approved under autonomy level {self._policy.level.value}.", risk

        return False, "DENY: Action fell through to default security DENY policy.", risk
