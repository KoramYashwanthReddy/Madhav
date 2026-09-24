"""Integration tests validating Module 15 PermissionGate & Module 16 Computer Control security boundaries."""

from datetime import UTC, datetime, timedelta

import pytest

from max.computer.backends.mock import MockComputerControlBackend
from max.computer.domain.action import ComputerActionRequest
from max.computer.domain.enums import (
    ComputerActionFailureReason,
    ComputerActionStatus,
    ComputerActionType,
)
from max.computer.repositories.action_repository import ComputerActionRepository
from max.computer.repositories.sequence_repository import ComputerSequenceRepository
from max.computer.repositories.trace_repository import ComputerTraceRepository
from max.computer.services.action_service import ComputerActionService
from max.computer.services.control_service import ComputerControlService
from max.computer.services.observation_service import ComputerObservationService
from max.config.settings import get_settings
from max.security.container import get_security_container, reset_security_container
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.decision import PermissionRequest
from max.security.domain.enums import PermissionAction, SecurityMode
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


@pytest.fixture
def setup_security_and_computer():
    reset_security_container()
    sec_container = get_security_container()

    backend = MockComputerControlBackend()
    action_repo = ComputerActionRepository()
    seq_repo = ComputerSequenceRepository()
    trace_repo = ComputerTraceRepository()
    settings = get_settings()

    obs_service = ComputerObservationService(backend=backend)
    act_service = ComputerActionService(
        backend=backend,
        action_repository=action_repo,
        sequence_repository=seq_repo,
        trace_repository=trace_repo,
        settings=settings,
        permission_gate=sec_container.gate,
    )
    ctrl_service = ComputerControlService(
        backend=backend,
        observation_service=obs_service,
        action_service=act_service,
        settings=settings,
    )
    return sec_container, ctrl_service, backend


def test_security_boundary_denied(setup_security_and_computer) -> None:
    """Section 71: Unauthorized request must fail and never execute backend action."""
    sec_container, ctrl_service, backend = setup_security_and_computer

    action_req = ComputerActionRequest(
        action_type=ComputerActionType.CLICK_MOUSE,
        parameters={"x": 100, "y": 100},
    )
    action = ctrl_service.execute_action(action_req, dry_run=False)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.PERMISSION_DENIED


def test_authorization_mismatch_action(setup_security_and_computer) -> None:
    """Section 72: Authorization for CLICK_MOUSE cannot be used for TYPE_TEXT."""
    sec_container, ctrl_service, backend = setup_security_and_computer

    auth_token = AuthorizedExecutionRequest(
        permission_decision_id="dec_click_101",
        tool_reference="computer.click_mouse",
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(resource_type="system", resource_id="mouse", owner_id="user"),
        subject=PermissionSubject(subject_type="AGENT", subject_id="agent_1"),
        owner_id="user",
        authorization_expiry=datetime.now(UTC) + timedelta(seconds=300),
    )

    action_req = ComputerActionRequest(
        action_type=ComputerActionType.TYPE_TEXT,
        parameters={"text": "hello"},
        permission_decision_id="dec_different_999",
    )

    action = ctrl_service.execute_action(action_req, auth_token=auth_token, dry_run=False)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.PERMISSION_DENIED


def test_authorization_expiration(setup_security_and_computer) -> None:
    """Section 74: Expired authorization token results in PERMISSION_EXPIRED."""
    sec_container, ctrl_service, backend = setup_security_and_computer

    expired_token = AuthorizedExecutionRequest(
        permission_decision_id="dec_exp_001",
        tool_reference="computer.move_mouse",
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(resource_type="system", resource_id="mouse", owner_id="user"),
        subject=PermissionSubject(subject_type="AGENT", subject_id="agent_1"),
        owner_id="user",
        authorization_expiry=datetime.now(UTC) - timedelta(seconds=1),
    )

    action_req = ComputerActionRequest(
        action_type=ComputerActionType.MOVE_MOUSE,
        parameters={"x": 50, "y": 50},
        permission_decision_id="dec_exp_001",
    )

    action = ctrl_service.execute_action(action_req, auth_token=expired_token, dry_run=False)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.PERMISSION_EXPIRED


def test_lockdown_mode_blocks_execution(setup_security_and_computer) -> None:
    """Section 75: Security LOCKDOWN mode prevents computer control execution."""
    sec_container, ctrl_service, backend = setup_security_and_computer

    sec_container.security_mode_service.set_mode(SecurityMode.LOCKDOWN, changed_by="user", reason="Security lockdown test")

    perm_req = PermissionRequest(
        owner_id="user",
        subject=PermissionSubject(subject_type="AGENT", subject_id="agent_1"),
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(resource_type="system", resource_id="keyboard", owner_id="user"),
    )
    decision = sec_container.gate.check(perm_req)
    assert decision.status.value in ("BLOCKED", "DENIED")


def test_emergency_block_stops_action(setup_security_and_computer) -> None:
    """Section 76: Emergency block ACTIVE prevents computer control execution."""
    sec_container, ctrl_service, backend = setup_security_and_computer

    sec_container.kill_switch_service.activate(activated_by="user", reason="Emergency stop test")

    perm_req = PermissionRequest(
        owner_id="user",
        subject=PermissionSubject(subject_type="AGENT", subject_id="agent_1"),
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(resource_type="system", resource_id="mouse", owner_id="user"),
    )
    decision = sec_container.gate.check(perm_req)
    assert decision.status.value in ("BLOCKED", "DENIED")
