"""Mandatory Critical Security Tests for Module 15 (Section 80 of specifications)."""

from datetime import UTC, datetime, timedelta

import pytest

from max.security.domain.approval import ApprovalDecision
from max.security.domain.decision import PermissionRequest, SecurityContext
from max.security.domain.enums import (
    ApprovalStatus,
    DecisionReason,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    PermissionGrantType,
    PermissionSubjectType,
    RiskLevel,
)
from max.security.domain.grant import PermissionGrant
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject, SecurityPrincipal
from max.security.repositories.approval_repository import InMemoryApprovalRepository
from max.security.repositories.permission_repository import InMemoryPermissionGrantRepository
from max.security.repositories.policy_repository import InMemoryPolicyRepository
from max.security.repositories.request_repository import (
    InMemoryPermissionDecisionRepository,
    InMemoryPermissionRequestRepository,
)
from max.security.services.approval_service import ApprovalService
from max.security.services.evaluator import PermissionEvaluator
from max.security.services.gate import PermissionGate
from max.security.services.kill_switch_service import KillSwitchService


@pytest.fixture
def security_setup():
    policy_repo = InMemoryPolicyRepository()
    grant_repo = InMemoryPermissionGrantRepository()
    req_repo = InMemoryPermissionRequestRepository()
    dec_repo = InMemoryPermissionDecisionRepository()
    appr_repo = InMemoryApprovalRepository()

    kill_switch = KillSwitchService(default_block=False)
    approval_service = ApprovalService(approval_repository=appr_repo, grant_repository=grant_repo)
    evaluator = PermissionEvaluator(policy_repository=policy_repo, grant_repository=grant_repo)

    gate = PermissionGate(
        evaluator=evaluator,
        request_repository=req_repo,
        decision_repository=dec_repo,
        kill_switch_service=kill_switch,
        approval_service=approval_service,
    )

    return {
        "policy_repo": policy_repo,
        "grant_repo": grant_repo,
        "evaluator": evaluator,
        "gate": gate,
        "kill_switch": kill_switch,
        "approval_service": approval_service,
    }


def test_critical_1_no_matching_policy(security_setup) -> None:
    """1. No matching policy -> DENIED (Default Deny)."""
    gate: PermissionGate = security_setup["gate"]

    req = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.AGENT, subject_id="agent_1"),
        action=PermissionAction.WRITE,
        resource=PermissionResource(
            resource_type="FILE", resource_id="/tmp/foo.txt", owner_id="owner_1"
        ),
        owner_id="owner_1",
    )
    decision = gate.check(req)
    assert decision.status == PermissionDecisionStatus.DENIED
    assert decision.reason == DecisionReason.NO_POLICY_MATCH


def test_critical_2_agent_capability_without_permission(security_setup) -> None:
    """2. Agent has capability but no permission -> DENIED."""
    gate: PermissionGate = security_setup["gate"]

    req = PermissionRequest(
        subject=PermissionSubject(
            subject_type=PermissionSubjectType.AGENT, subject_id="coding_agent"
        ),
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(
            resource_type="TERMINAL", resource_id="shell", owner_id="owner_1"
        ),
        owner_id="owner_1",
        risk_level=RiskLevel.CRITICAL,
    )
    decision = gate.check(req)
    assert decision.status == PermissionDecisionStatus.DENIED


def test_critical_3_tool_active_without_permission(security_setup) -> None:
    """3. Tool is active but no permission -> DENIED."""
    gate: PermissionGate = security_setup["gate"]

    req = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1"),
        tool_reference="filesystem.read",
        action=PermissionAction.READ,
        resource=PermissionResource(
            resource_type="FILE", resource_id="/etc/shadow", owner_id="owner_1"
        ),
        owner_id="owner_1",
    )
    decision = gate.check(req)
    assert decision.status == PermissionDecisionStatus.DENIED


def test_critical_4_expired_permission_grant(security_setup) -> None:
    """4. Permission expired -> DENIED."""
    grant_repo: InMemoryPermissionGrantRepository = security_setup["grant_repo"]
    evaluator: PermissionEvaluator = security_setup["evaluator"]

    subject = PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/proj/doc.txt", owner_id="owner_1"
    )

    # Create expired grant
    now = datetime.now(UTC)
    expired_grant = PermissionGrant(
        subject=subject,
        action=PermissionAction.READ,
        resource=resource,
        grant_type=PermissionGrantType.TIME_LIMITED,
        owner_id="owner_1",
        expires_at=now - timedelta(seconds=100),
    )
    grant_repo.save(expired_grant)

    principal = SecurityPrincipal(subject=subject, owner_id="owner_1")
    context = SecurityContext(
        principal=principal,
        owner_id="owner_1",
        action=PermissionAction.READ,
        resource=resource,
    )

    decision = evaluator.evaluate(context, request_id="req_expired")
    assert decision.status == PermissionDecisionStatus.DENIED


def test_critical_5_emergency_block_active(security_setup) -> None:
    """5. Emergency block active -> BLOCKED."""
    gate: PermissionGate = security_setup["gate"]
    kill_switch: KillSwitchService = security_setup["kill_switch"]

    kill_switch.activate(activated_by="admin", reason="Security breach")

    req = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1"),
        action=PermissionAction.READ,
        resource=PermissionResource(
            resource_type="FILE", resource_id="/proj/doc.txt", owner_id="owner_1"
        ),
        owner_id="owner_1",
    )
    decision = gate.check(req)
    assert decision.status == PermissionDecisionStatus.BLOCKED
    assert decision.reason == DecisionReason.EMERGENCY_BLOCK


def test_critical_6_owner_mismatch(security_setup) -> None:
    """6. Owner mismatch -> DENIED."""
    evaluator: PermissionEvaluator = security_setup["evaluator"]

    subject = PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1")
    principal = SecurityPrincipal(subject=subject, owner_id="user_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/private/doc.txt", owner_id="user_2"
    )  # Mismatch

    context = SecurityContext(
        principal=principal,
        owner_id="user_1",
        action=PermissionAction.READ,
        resource=resource,
    )

    decision = evaluator.evaluate(context, request_id="req_mismatch")
    assert decision.status == PermissionDecisionStatus.DENIED
    assert decision.reason == DecisionReason.OWNER_MISMATCH


def test_critical_7_evaluator_exception_fail_closed(security_setup) -> None:
    """7. Policy evaluator throws exception -> DENIED / ERROR (Fail Closed)."""

    class BrokenRepo:
        def list_policies(self, **kwargs):
            raise RuntimeError("Database connection lost!")

    broken_evaluator = PermissionEvaluator(policy_repository=BrokenRepo())  # type: ignore[arg-type]

    subject = PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="user_1")
    principal = SecurityPrincipal(subject=subject, owner_id="owner_1")
    resource = PermissionResource(
        resource_type="FILE", resource_id="/proj/doc.txt", owner_id="owner_1"
    )
    context = SecurityContext(
        principal=principal,
        owner_id="owner_1",
        action=PermissionAction.READ,
        resource=resource,
    )

    decision = broken_evaluator.evaluate(context, request_id="req_broken")
    assert decision.status == PermissionDecisionStatus.ERROR
    assert decision.effect == PermissionEffect.DENY
    assert decision.reason == DecisionReason.EVALUATION_ERROR


def test_critical_8_approval_not_granted(security_setup) -> None:
    """8. Approval not granted -> NOT AUTHORIZED / REQUIRES_APPROVAL."""
    gate: PermissionGate = security_setup["gate"]

    # Request requiring approval
    req = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.AGENT, subject_id="agent_1"),
        action=PermissionAction.WRITE,
        resource=PermissionResource(
            resource_type="FILE", resource_id="/proj/main.py", owner_id="owner_1"
        ),
        owner_id="owner_1",
        risk_level=RiskLevel.HIGH,
    )

    # First check requires approval
    decision, token = gate.check_and_authorize(req)
    assert decision.status in {
        PermissionDecisionStatus.DENIED,
        PermissionDecisionStatus.REQUIRES_APPROVAL,
    }
    assert token is None


def test_critical_9_approval_for_different_resource(security_setup) -> None:
    """9. Approval granted for resource A does not authorize resource B -> DENIED."""
    appr_service: ApprovalService = security_setup["approval_service"]
    gate: PermissionGate = security_setup["gate"]

    res_a = PermissionResource(
        resource_type="FILE", resource_id="/proj/fileA.py", owner_id="owner_1"
    )
    res_b = PermissionResource(
        resource_type="FILE", resource_id="/proj/fileB.py", owner_id="owner_1"
    )

    # Create approval for res_a and approve it
    appr_req = appr_service.create_approval_request(
        permission_request_id="req_a",
        title="Approve file A",
        explanation="Testing resource isolation",
        risk_level=RiskLevel.HIGH,
        requested_action=PermissionAction.WRITE,
        requested_resource=res_a,
        owner_id="owner_1",
    )
    appr_service.submit_decision(
        ApprovalDecision(
            approval_id=appr_req.approval_id, status=ApprovalStatus.APPROVED, decided_by="owner_1"
        )
    )

    # Now attempt action on res_b
    req_b = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="owner_1"),
        action=PermissionAction.WRITE,
        resource=res_b,
        owner_id="owner_1",
    )

    decision = gate.check(req_b)
    assert decision.status == PermissionDecisionStatus.DENIED


def test_critical_10_approval_for_different_tool(security_setup) -> None:
    """10. Approval for tool A does not authorize tool B -> DENIED."""
    appr_service: ApprovalService = security_setup["approval_service"]
    gate: PermissionGate = security_setup["gate"]

    res = PermissionResource(
        resource_type="FILE", resource_id="/proj/script.py", owner_id="owner_1"
    )

    # Create approval for tool 'filesystem.read' and approve it
    appr_req = appr_service.create_approval_request(
        permission_request_id="req_tool",
        title="Approve read",
        explanation="Testing tool isolation",
        risk_level=RiskLevel.MEDIUM,
        requested_action=PermissionAction.READ,
        requested_resource=res,
        owner_id="owner_1",
    )
    appr_service.submit_decision(
        ApprovalDecision(
            approval_id=appr_req.approval_id, status=ApprovalStatus.APPROVED, decided_by="owner_1"
        )
    )

    # Now attempt tool 'terminal.execute' action
    req_term = PermissionRequest(
        subject=PermissionSubject(subject_type=PermissionSubjectType.USER, subject_id="owner_1"),
        tool_reference="terminal.execute",
        action=PermissionAction.EXECUTE,
        resource=res,
        owner_id="owner_1",
    )

    decision = gate.check(req_term)
    assert decision.status == PermissionDecisionStatus.DENIED
