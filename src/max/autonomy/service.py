"""Centralized Autonomy Facade Service for Module 41 — Future Autonomous Intelligence."""

import logging
from typing import Any

from max.autonomy.approval import ApprovalService
from max.autonomy.budget import AutonomyBudgetService
from max.autonomy.domain import (
    ApprovalRequest,
    AutonomyHealth,
    AutonomyLevel,
    AutonomyPolicy,
    Mission,
    MissionAction,
    MissionResult,
    MissionStatus,
    ResourceBudget,
    RiskLevel,
)
from max.autonomy.orchestrator import MissionOrchestrator
from max.autonomy.policy import AutonomyPolicyService
from max.autonomy.simulation import AutonomySimulationService
from max.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class AutonomyService:
    """Centralized facade coordinating autonomy policies, missions, approvals, budgets, kill switches, and simulations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.policy_service = AutonomyPolicyService(self.settings)
        self.approval_service = ApprovalService(self.settings)
        self.budget_service = AutonomyBudgetService(self.settings)
        self.orchestrator = MissionOrchestrator(
            policy_service=self.policy_service,
            approval_service=self.approval_service,
            budget_service=self.budget_service,
            settings=self.settings,
        )
        self.simulation_service = AutonomySimulationService(
            policy_service=self.policy_service,
            approval_service=self.approval_service,
            budget_service=self.budget_service,
            orchestrator=self.orchestrator,
            settings=self.settings,
        )
        self._missions: dict[str, Mission] = {}

    def get_policy(self) -> AutonomyPolicy:
        """Get active global autonomy policy."""
        return self.policy_service.policy

    def update_policy(self, updates: dict[str, Any]) -> AutonomyPolicy:
        """Update global governance policy parameters."""
        return self.policy_service.update_policy(updates)

    def set_kill_switch(self, active: bool) -> bool:
        """Activate or deactivate emergency kill switch."""
        return self.policy_service.set_kill_switch(active)

    def create_mission(
        self,
        title: str,
        objective: str,
        owner_id: str = "user_admin",
        autonomy_level: AutonomyLevel = AutonomyLevel.SUPERVISED,
        allowed_scope: list[str] | None = None,
        budget: ResourceBudget | None = None,
        actions: list[MissionAction] | None = None,
    ) -> Mission:
        """Create and register new mission entity."""
        mission_id = f"mission_{len(self._missions) + 1}"
        m = Mission(
            mission_id=mission_id,
            owner_id=owner_id,
            title=title,
            objective=objective,
            status=MissionStatus.DRAFT,
            autonomy_level=autonomy_level,
            allowed_scope=allowed_scope or ["data/*", "artifacts/*", "docs/*"],
            budget=budget or ResourceBudget(),
            actions=actions or [],
        )
        self._missions[mission_id] = m
        logger.info("Created mission %s: '%s'.", mission_id, title)
        return m

    def get_mission(self, mission_id: str) -> Mission:
        """Retrieve mission by ID."""
        if mission_id not in self._missions:
            raise ValueError(f"Mission '{mission_id}' not found.")
        return self._missions[mission_id]

    def list_missions(self, status: str | None = None) -> list[Mission]:
        """List registered missions with optional status filtering."""
        if status:
            return [m for m in self._missions.values() if m.status.value == status.upper()]
        return list(self._missions.values())

    def run_mission(self, mission_id: str) -> MissionResult:
        """Execute autonomous mission loop for target mission ID."""
        mission = self.get_mission(mission_id)
        return self.orchestrator.run_mission(mission)

    def pause_mission(self, mission_id: str) -> Mission:
        """Pause a running mission."""
        mission = self.get_mission(mission_id)
        if mission.status == MissionStatus.RUNNING:
            mission.status = MissionStatus.PAUSED
            logger.info("Paused mission %s.", mission_id)
        return mission

    def resume_mission(self, mission_id: str) -> MissionResult:
        """Resume a paused mission."""
        mission = self.get_mission(mission_id)
        if mission.status in (MissionStatus.PAUSED, MissionStatus.WAITING_FOR_USER):
            mission.status = MissionStatus.RUNNING
            logger.info("Resumed mission %s.", mission_id)
            return self.orchestrator.run_mission(mission)
        raise ValueError(f"Cannot resume mission '{mission_id}' in status '{mission.status.value}'.")

    def cancel_mission(self, mission_id: str) -> Mission:
        """Cancel a mission."""
        mission = self.get_mission(mission_id)
        mission.status = MissionStatus.CANCELLED
        logger.info("Cancelled mission %s.", mission_id)
        return mission

    def list_pending_approvals(self, mission_id: str | None = None) -> list[ApprovalRequest]:
        """List unresolved pending approval requests."""
        return self.approval_service.list_pending_approvals(mission_id)

    def approve_request(self, approval_id: str, user_id: str = "user_admin") -> ApprovalRequest:
        """Approve pending action request."""
        return self.approval_service.approve_request(approval_id, user_id)

    def deny_request(self, approval_id: str, user_id: str = "user_admin") -> ApprovalRequest:
        """Deny pending action request."""
        return self.approval_service.deny_request(approval_id, user_id)

    def dry_run_mission(self, mission_id: str) -> dict[str, Any]:
        """Run dry-run simulation on specified mission."""
        mission = self.get_mission(mission_id)
        return self.simulation_service.dry_run_mission(mission)

    def run_safety_tests(self) -> dict[str, Any]:
        """Execute comprehensive safety test suite (prompt injection, scope escape, restart recovery)."""
        inj_res = self.simulation_service.run_prompt_injection_test()
        scope_res = self.simulation_service.run_scope_escape_test()
        rec_res = self.simulation_service.run_restart_recovery_test()

        all_passed = inj_res["passed"] and scope_res["passed"] and rec_res["passed"]

        return {
            "all_tests_passed": all_passed,
            "prompt_injection": inj_res,
            "scope_escape": scope_res,
            "restart_recovery": rec_res,
        }

    def get_health(self) -> AutonomyHealth:
        """Retrieve diagnostic telemetry metrics for Module 41."""
        active = sum(1 for m in self._missions.values() if m.status in (MissionStatus.RUNNING, MissionStatus.QUEUED))
        completed = sum(1 for m in self._missions.values() if m.status == MissionStatus.COMPLETED)
        failed = sum(1 for m in self._missions.values() if m.status == MissionStatus.FAILED)
        blocked = sum(1 for m in self._missions.values() if m.status in (MissionStatus.BLOCKED, MissionStatus.WAITING_FOR_USER))
        pending_appr = len(self.approval_service.list_pending_approvals())

        return AutonomyHealth(
            active_missions=active,
            completed_missions=completed,
            failed_missions=failed,
            blocked_missions=blocked,
            pending_approvals=pending_appr,
            kill_switch_active=self.policy_service.is_kill_switch_active(),
            circuit_breaker_tripped=self.orchestrator.circuit_breaker.is_tripped,
        )


_autonomy_service_instance: AutonomyService | None = None


def get_autonomy_service() -> AutonomyService:
    """Retrieve global singleton AutonomyService instance."""
    global _autonomy_service_instance
    if _autonomy_service_instance is None:
        _autonomy_service_instance = AutonomyService()
    return _autonomy_service_instance
