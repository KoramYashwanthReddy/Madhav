"""Unit tests for Autonomy Safety, Simulation, and Resistance Tests."""

from max.autonomy.approval import ApprovalService
from max.autonomy.budget import AutonomyBudgetService
from max.autonomy.orchestrator import MissionOrchestrator
from max.autonomy.policy import AutonomyPolicyService
from max.autonomy.simulation import AutonomySimulationService


def test_simulation_safety_suite() -> None:
    pol_svc = AutonomyPolicyService()
    appr_svc = ApprovalService()
    bud_svc = AutonomyBudgetService()
    orchestrator = MissionOrchestrator(pol_svc, appr_svc, bud_svc)
    sim_svc = AutonomySimulationService(pol_svc, appr_svc, bud_svc, orchestrator)

    inj_res = sim_svc.run_prompt_injection_test()
    assert inj_res["passed"]
    assert inj_res["blocked_count"] == inj_res["total_samples"]

    scope_res = sim_svc.run_scope_escape_test()
    assert scope_res["passed"]

    rec_res = sim_svc.run_restart_recovery_test()
    assert rec_res["passed"]
    assert rec_res["recovered_status"] == "PAUSED"
