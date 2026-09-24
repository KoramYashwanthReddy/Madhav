"""Unit tests for Module 15 domain models and exceptions."""

from datetime import UTC, datetime, timedelta

from max.security.domain.action import ActionDefinition
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.enums import (
    PermissionAction,
    PermissionGrantType,
    PermissionSubjectType,
    ResourceSensitivity,
    RiskLevel,
)
from max.security.domain.exceptions import (
    EmergencyBlockError,
    PermissionDeniedError,
    PermissionRequiredError,
)
from max.security.domain.grant import PermissionGrant
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject, SecurityPrincipal


def test_permission_subject_and_principal() -> None:
    subject = PermissionSubject(
        subject_type=PermissionSubjectType.AGENT,
        subject_id="agent_coding_01",
        name="Coding Agent",
    )
    assert subject.subject_type == PermissionSubjectType.AGENT
    assert subject.subject_id == "agent_coding_01"

    principal = SecurityPrincipal(
        subject=subject,
        owner_id="user_owner_1",
        roles=["agent"],
    )
    assert principal.owner_id == "user_owner_1"
    assert principal.principal_id.startswith("prn_")


def test_permission_resource_and_action() -> None:
    resource = PermissionResource(
        resource_type="FILE",
        resource_id="/project/src/main.py",
        location="/project/src/main.py",
        owner_id="user_owner_1",
        sensitivity=ResourceSensitivity.HIGHLY_SENSITIVE,
    )
    assert resource.resource_type == "FILE"
    assert resource.sensitivity == ResourceSensitivity.HIGHLY_SENSITIVE

    action_def = ActionDefinition(
        action=PermissionAction.WRITE,
        description="Write or overwrite file contents",
        risk_level=RiskLevel.HIGH,
    )
    assert action_def.action == PermissionAction.WRITE
    assert action_def.risk_level == RiskLevel.HIGH


def test_permission_grant_active_property() -> None:
    subject = PermissionSubject(
        subject_type=PermissionSubjectType.USER,
        subject_id="user_1",
    )
    resource = PermissionResource(
        resource_type="FILE",
        resource_id="/project/readme.md",
        owner_id="user_1",
    )
    grant = PermissionGrant(
        subject=subject,
        action=PermissionAction.READ,
        resource=resource,
        grant_type=PermissionGrantType.ONE_TIME,
        owner_id="user_1",
    )
    assert grant.is_active is True

    # After consumption
    used_grant = grant.model_copy(update={"used_count": 1})
    assert used_grant.is_active is False

    # After revocation
    revoked_grant = grant.model_copy(update={"revoked_at": datetime.now(UTC)})
    assert revoked_grant.is_active is False


def test_authorized_execution_request_validation() -> None:
    subject = PermissionSubject(
        subject_type=PermissionSubjectType.USER,
        subject_id="user_1",
    )
    resource = PermissionResource(
        resource_type="FILE",
        resource_id="/project/readme.md",
        owner_id="user_1",
    )
    now = datetime.now(UTC)
    token = AuthorizedExecutionRequest(
        permission_decision_id="dec_123",
        action=PermissionAction.READ,
        resource=resource,
        subject=subject,
        owner_id="user_1",
        authorization_expiry=now + timedelta(minutes=5),  # future expiry
    )
    assert token.is_valid is True


def test_security_exceptions() -> None:
    err = PermissionDeniedError("Denied access")
    assert err.code == "PERMISSION_DENIED"
    assert err.status_code == 403

    err_req = PermissionRequiredError("Approval needed")
    assert err_req.code == "APPROVAL_REQUIRED"

    err_block = EmergencyBlockError("Blocked")
    assert err_block.code == "EMERGENCY_BLOCK_ACTIVE"
