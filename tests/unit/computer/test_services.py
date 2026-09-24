"""Unit tests for computer control services, safety limits, and execution."""

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
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.domain.enums import PermissionAction
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject


@pytest.fixture
def service_setup():
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
    )
    ctrl_service = ComputerControlService(
        backend=backend,
        observation_service=obs_service,
        action_service=act_service,
        settings=settings,
    )
    return ctrl_service, trace_repo


def test_dry_run_execution(service_setup) -> None:
    """Test dry-run execution returns SIMULATED status without hardware mutation."""
    ctrl_service, trace_repo = service_setup
    req = ComputerActionRequest(
        action_type=ComputerActionType.MOVE_MOUSE,
        parameters={"x": 500, "y": 500},
        permission_decision_id="dec_123",
    )
    action = ctrl_service.execute_action(req, dry_run=True)
    assert action.status == ComputerActionStatus.SIMULATED
    assert action.result is not None
    assert action.result.status == ComputerActionStatus.SIMULATED

    # Verify trace recorded
    events = trace_repo.list_events(action_id=action.action_id)
    assert any(e.event_type == "ACTION_SIMULATED" for e in events)


def test_safety_bounds_validation(service_setup) -> None:
    """Test negative coordinates trigger OutOfBoundsError failure."""
    ctrl_service, _ = service_setup
    req = ComputerActionRequest(
        action_type=ComputerActionType.MOVE_MOUSE,
        parameters={"x": -50, "y": 100},
    )
    action = ctrl_service.execute_action(req, dry_run=True)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.INVALID_PARAMETERS


def test_missing_permission_decision(service_setup) -> None:
    """Test state-changing action fails without authorization token or decision ID."""
    ctrl_service, _ = service_setup
    req = ComputerActionRequest(
        action_type=ComputerActionType.CLICK_MOUSE,
        parameters={"x": 100, "y": 100},
    )
    # Perform in non-dry run mode to hit permission verification
    action = ctrl_service.execute_action(req, dry_run=False)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.PERMISSION_DENIED


def test_expired_authorization_token(service_setup) -> None:
    """Test expired AuthorizedExecutionRequest is rejected."""
    ctrl_service, _ = service_setup
    req = ComputerActionRequest(
        action_type=ComputerActionType.TYPE_TEXT,
        parameters={"text": "hello"},
        permission_decision_id="dec_456",
    )
    expired_token = AuthorizedExecutionRequest(
        permission_decision_id="dec_456",
        action=PermissionAction.EXECUTE,
        resource=PermissionResource(resource_type="system", resource_id="keyboard", owner_id="user_1"),
        subject=PermissionSubject(subject_type="AGENT", subject_id="agent_1"),
        owner_id="user_1",
        authorization_expiry=datetime.now(UTC) - timedelta(seconds=10),
    )
    action = ctrl_service.execute_action(req, auth_token=expired_token, dry_run=False)
    assert action.status == ComputerActionStatus.FAILED
    assert action.failure is not None
    assert action.failure.reason == ComputerActionFailureReason.PERMISSION_EXPIRED


def test_sensitive_text_redaction_in_trace(service_setup) -> None:
    """Test typed text parameters are redacted from trace logs."""
    ctrl_service, trace_repo = service_setup
    req = ComputerActionRequest(
        action_type=ComputerActionType.TYPE_TEXT,
        parameters={"text": "super_secret_password"},
        permission_decision_id="dec_789",
    )
    action = ctrl_service.execute_action(req, dry_run=True)
    assert action.status == ComputerActionStatus.SIMULATED

    events = trace_repo.list_events(action_id=action.action_id)
    req_event = next(e for e in events if e.event_type == "ACTION_REQUESTED")
    params = req_event.details
    assert "super_secret_password" not in str(params)
    assert "[REDACTED" in str(params)
