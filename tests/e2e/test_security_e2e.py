"""End-to-End acceptance flow tests for Module 15 — Permission & Security."""

import pytest

from max.security.container import SecurityContainer, reset_security_container
from max.security.domain.approval import ApprovalDecision
from max.security.domain.decision import PermissionRequest
from max.security.domain.enums import (
    ApprovalStatus,
    PermissionAction,
    PermissionDecisionStatus,
    PermissionEffect,
    PermissionScope,
    PermissionSubjectType,
    RiskLevel,
    SecurityMode,
)
from max.security.domain.permission import PermissionCondition, PermissionRule
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


@pytest.fixture(autouse=True)
def cleanup():
    reset_security_container()
    yield
    reset_security_container()


def test_e2e_permission_security_acceptance_flow() -> None:
    """Full E2E acceptance flow: Policy creation, evaluation, approval workflow, grants, emergency block."""
    container = SecurityContainer()

    # 1. Create a policy requiring approval for HIGH risk WRITE actions
    container.policy_service.create_policy(
        name="Require Approval for High Risk Write",
        owner_id="user_owner_1",
        priority=100,
        scope=PermissionScope.GLOBAL,
        rules=[
            PermissionRule(
                effect=PermissionEffect.REQUIRE_APPROVAL,
                priority=10,
                reason="High risk write operations need user confirmation",
                action_conditions=[
                    PermissionCondition(field="action", operator="EQUALS", value="WRITE")
                ],
            )
        ],
    )

    # 2. Agent submits a PermissionRequest for WRITE on /project/src/main.py
    subject = PermissionSubject(
        subject_type=PermissionSubjectType.AGENT, subject_id="coding_agent_1"
    )
    resource = PermissionResource(
        resource_type="FILE", resource_id="/project/src/main.py", owner_id="user_owner_1"
    )
    request = PermissionRequest(
        subject=subject,
        tool_reference="filesystem.write",
        action=PermissionAction.WRITE,
        resource=resource,
        owner_id="user_owner_1",
        risk_level=RiskLevel.HIGH,
    )

    # 3. Check gate -> expects REQUIRES_APPROVAL and generates an ApprovalRequest ID
    decision, token = container.gate.check_and_authorize(request)
    assert decision.status == PermissionDecisionStatus.REQUIRES_APPROVAL
    assert decision.approval_required is True
    assert decision.approval_request_id is not None
    assert token is None  # Execution boundary token MUST NOT be issued yet!

    # 4. Human user retrieves pending approval and approves it
    approval_id = decision.approval_request_id
    approval_item = container.approval_service.get_approval(approval_id)
    assert approval_item.status == ApprovalStatus.PENDING

    container.approval_service.submit_decision(
        ApprovalDecision(
            approval_id=approval_id,
            status=ApprovalStatus.APPROVED,
            decided_by="user_owner_1",
            reason="User confirmed modification to main.py",
        )
    )

    # 5. Re-check gate -> now expects ALLOWED and valid AuthorizedExecutionRequest token!
    decision_after_approval, token_after_approval = container.gate.check_and_authorize(request)
    assert decision_after_approval.status == PermissionDecisionStatus.ALLOWED
    assert token_after_approval is not None
    assert token_after_approval.is_valid is True
    assert token_after_approval.permission_decision_id == decision_after_approval.decision_id

    # 6. Activate Kill Switch Emergency Block
    container.kill_switch_service.activate(
        activated_by="user_owner_1", reason="Emergency threat detected"
    )

    # 7. Check gate during emergency block -> expects BLOCKED
    decision_during_emergency, token_during_emergency = container.gate.check_and_authorize(request)
    assert decision_during_emergency.status == PermissionDecisionStatus.BLOCKED
    assert token_during_emergency is None

    # 8. Deactivate Emergency Block
    container.kill_switch_service.deactivate(
        deactivated_by="user_owner_1", reason="Threat resolved"
    )
    mode_state = container.security_mode_service.get_mode()
    assert mode_state.mode == SecurityMode.NORMAL
