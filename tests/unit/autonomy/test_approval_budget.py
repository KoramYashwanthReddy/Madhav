"""Unit tests for Approval Service and Autonomy Budget Enforcement."""

import pytest
from max.autonomy.approval import ApprovalService
from max.autonomy.budget import AutonomyBudgetService, MissionCircuitBreaker
from max.autonomy.domain import ApprovalStatus, Mission, MissionStatus, ResourceBudget, RiskLevel


def test_approval_request_lifecycle() -> None:
    appr_svc = ApprovalService()
    mission = Mission(mission_id="m1", title="Test", objective="Obj")

    req = appr_svc.create_approval_request(
        mission=mission,
        action_name="send_email",
        risk_level=RiskLevel.HIGH,
        reason="Requires user review",
        impact_summary="Sends message to external user",
        timeout_seconds=600,
    )

    assert req.status == ApprovalStatus.PENDING
    assert len(appr_svc.list_pending_approvals()) == 1

    approved = appr_svc.approve_request(req.approval_id, user_id="admin_user")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.approved_by == "admin_user"
    assert len(appr_svc.list_pending_approvals()) == 0


def test_budget_enforcement_tool_calls_exceeded() -> None:
    bud_svc = AutonomyBudgetService()
    mission = Mission(
        mission_id="m1",
        title="Test",
        objective="Obj",
        budget=ResourceBudget(max_tool_calls=2),
    )

    ok1, msg1 = bud_svc.record_usage(mission, tool_calls=2)
    assert ok1

    ok2, msg2 = bud_svc.record_usage(mission, tool_calls=1)
    assert not ok2
    assert "BUDGET_EXCEEDED" in msg2
    assert mission.status == MissionStatus.BLOCKED


def test_circuit_breaker_tripping() -> None:
    cb = MissionCircuitBreaker(failure_threshold=3)

    assert not cb.record_failure()
    assert not cb.record_failure()
    assert cb.record_failure()  # 3rd failure trips
    assert cb.is_tripped

    cb.reset()
    assert not cb.is_tripped
