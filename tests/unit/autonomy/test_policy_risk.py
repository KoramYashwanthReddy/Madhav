"""Unit tests for Autonomy Risk Classification and 10-tier Policy Hierarchy."""

from max.autonomy.domain import Mission, RiskLevel
from max.autonomy.policy import AutonomyPolicyService, AutonomyRiskService


def test_risk_classification() -> None:
    risk_svc = AutonomyRiskService()

    assert risk_svc.classify_risk("read_file", "docs/test.txt") == RiskLevel.LOW
    assert risk_svc.classify_risk("create_draft", "artifacts/doc.md") == RiskLevel.MEDIUM
    assert risk_svc.classify_risk("send_email", "user@example.com") == RiskLevel.HIGH
    assert risk_svc.classify_risk("delete_database", "production_db") == RiskLevel.CRITICAL
    assert risk_svc.classify_risk("grant_permission", "user_1") == RiskLevel.CRITICAL


def test_policy_hierarchy_kill_switch() -> None:
    pol_svc = AutonomyPolicyService()
    pol_svc.set_kill_switch(True)

    mission = Mission(mission_id="m1", title="Test", objective="Obj")
    allowed, reason, risk = pol_svc.evaluate_action_authorization(
        mission=mission, action_name="read_file", target_resource="data/test.txt"
    )

    assert not allowed
    assert "kill-switch is ACTIVE" in reason


def test_policy_hierarchy_blocked_action() -> None:
    pol_svc = AutonomyPolicyService()
    mission = Mission(mission_id="m1", title="Test", objective="Obj")

    allowed, reason, risk = pol_svc.evaluate_action_authorization(
        mission=mission, action_name="delete_files", target_resource="data/old.txt"
    )

    assert not allowed
    assert "blocked action pattern" in reason


def test_policy_hierarchy_scope_escape() -> None:
    pol_svc = AutonomyPolicyService()
    mission = Mission(
        mission_id="m1",
        title="Test",
        objective="Obj",
        allowed_scope=["data/*", "artifacts/*"],
    )

    allowed, reason, risk = pol_svc.evaluate_action_authorization(
        mission=mission, action_name="read_file", target_resource="C:/Windows/System32/cmd.exe"
    )

    assert not allowed
    assert "escapes mission scope" in reason
