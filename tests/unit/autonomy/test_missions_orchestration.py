"""Unit tests for Mission Orchestration, Execution Loop, and Verification."""

import pytest
from max.autonomy.approval import ApprovalService
from max.autonomy.budget import AutonomyBudgetService
from max.autonomy.domain import ActionStatus, AutonomyLevel, Mission, MissionAction, MissionStatus, ResourceBudget, RiskLevel
from max.autonomy.orchestrator import MissionOrchestrator, MissionVerificationService
from max.autonomy.policy import AutonomyPolicyService


def test_mission_orchestration_successful_run() -> None:
    pol_svc = AutonomyPolicyService()
    appr_svc = ApprovalService()
    bud_svc = AutonomyBudgetService()
    orchestrator = MissionOrchestrator(pol_svc, appr_svc, bud_svc)

    mission = Mission(
        mission_id="m_test_1",
        title="Test Mission",
        objective="Analyze files and create report",
        autonomy_level=AutonomyLevel.SUPERVISED,
        allowed_scope=["data/*", "artifacts/*"],
        budget=ResourceBudget(max_tool_calls=10),
        actions=[
            MissionAction(
                action_id="act_1",
                mission_id="m_test_1",
                step_number=1,
                tool_id="search_files",
                arguments={"path": "data/sample.txt"},
                risk_level=RiskLevel.LOW,
            )
        ],
    )

    result = orchestrator.run_mission(mission)

    assert result.status == MissionStatus.COMPLETED
    assert result.verification_passed
    assert result.completed_steps_count == 1
    assert len(result.evidence) > 0


def test_action_empirical_verification() -> None:
    v_svc = MissionVerificationService()
    success_action = MissionAction(
        action_id="a1",
        mission_id="m1",
        step_number=1,
        tool_id="read_file",
        status=ActionStatus.RUNNING,
        result={"status": "success", "content": "hello world"},
    )

    ok, evidence = v_svc.verify_action_result(success_action)
    assert ok
    assert "Verified action" in evidence
