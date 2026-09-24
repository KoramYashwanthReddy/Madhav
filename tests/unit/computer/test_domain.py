"""Unit tests for computer control domain models, value objects, and lifecycle states."""

from max.computer.domain.action import (
    ComputerActionRequest,
    ComputerActionSequence,
)
from max.computer.domain.enums import (
    ComputerActionStatus,
    ComputerActionType,
)
from max.computer.domain.models import ScreenRegion


def test_screen_region_validation() -> None:
    """Test valid and invalid screen region bounds."""
    valid_region = ScreenRegion(x=0, y=0, width=1920, height=1080)
    assert valid_region.is_valid() is True

    invalid_region = ScreenRegion(x=10, y=10, width=0, height=100)
    assert invalid_region.is_valid() is False


def test_computer_action_request_creation() -> None:
    """Test computer action request instantiation."""
    req = ComputerActionRequest(
        action_type=ComputerActionType.CLICK_MOUSE,
        parameters={"x": 100, "y": 200, "button": "left"},
        owner_id="user_1",
    )
    assert req.action_type == ComputerActionType.CLICK_MOUSE
    assert req.parameters["x"] == 100
    assert req.action_id.startswith("cact_")


def test_action_sequence_validation() -> None:
    """Test action sequence structure."""
    req1 = ComputerActionRequest(action_type=ComputerActionType.MOVE_MOUSE, parameters={"x": 10, "y": 10})
    req2 = ComputerActionRequest(action_type=ComputerActionType.CLICK_MOUSE, parameters={"button": "left"})
    seq = ComputerActionSequence(actions=[req1, req2], stop_on_failure=True)

    assert len(seq.actions) == 2
    assert seq.sequence_id.startswith("seq_")
    assert seq.status == ComputerActionStatus.CREATED
