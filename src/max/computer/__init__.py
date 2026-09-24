"""Module 16 — Computer Control package."""

from max.computer.container import (
    ComputerContainer,
    get_computer_container,
    reset_computer_container,
)
from max.computer.domain.action import (
    ComputerAction,
    ComputerActionFailure,
    ComputerActionRequest,
    ComputerActionResult,
    ComputerActionSequence,
)
from max.computer.domain.enums import (
    ComputerActionFailureReason,
    ComputerActionStatus,
    ComputerActionType,
    ComputerCapability,
    KeyboardKey,
    KeyboardModifier,
    MouseButton,
    PlatformType,
)
from max.computer.domain.exceptions import (
    BackendUnavailableError,
    ComputerActionCancelledError,
    ComputerActionTimeoutError,
    ComputerControlError,
    ComputerPermissionError,
    ComputerSecurityBlockedError,
    ComputerVerificationError,
    DisplayNotFoundError,
    InvalidComputerActionError,
    OutOfBoundsError,
    WindowNotFoundError,
)
from max.computer.domain.models import (
    ComputerState,
    ComputerTraceEvent,
    CursorPosition,
    DisplayInfo,
    InputDeviceState,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)
from max.computer.services.action_service import ComputerActionService
from max.computer.services.control_service import ComputerControlService
from max.computer.services.observation_service import ComputerObservationService

__all__ = [
    # Domain Enums
    "ComputerActionType",
    "ComputerActionStatus",
    "ComputerActionFailureReason",
    "MouseButton",
    "KeyboardKey",
    "KeyboardModifier",
    "ComputerCapability",
    "PlatformType",
    # Domain Models
    "DisplayInfo",
    "ScreenRegion",
    "ScreenCapture",
    "CursorPosition",
    "WindowInfo",
    "InputDeviceState",
    "ComputerState",
    "ComputerTraceEvent",
    "ComputerActionRequest",
    "ComputerActionResult",
    "ComputerActionFailure",
    "ComputerAction",
    "ComputerActionSequence",
    # Exceptions
    "ComputerControlError",
    "BackendUnavailableError",
    "DisplayNotFoundError",
    "WindowNotFoundError",
    "InvalidComputerActionError",
    "OutOfBoundsError",
    "ComputerPermissionError",
    "ComputerSecurityBlockedError",
    "ComputerActionTimeoutError",
    "ComputerActionCancelledError",
    "ComputerVerificationError",
    # Services & Container
    "ComputerObservationService",
    "ComputerActionService",
    "ComputerControlService",
    "ComputerContainer",
    "get_computer_container",
    "reset_computer_container",
]
