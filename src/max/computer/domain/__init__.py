"""Domain models for Module 16 — Computer Control."""

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

__all__ = [
    # Enums
    "ComputerActionType",
    "ComputerActionStatus",
    "ComputerActionFailureReason",
    "MouseButton",
    "KeyboardKey",
    "KeyboardModifier",
    "ComputerCapability",
    "PlatformType",
    # Domain models
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
    "ComputerVerificationError",
    "ComputerActionTimeoutError",
    "ComputerActionCancelledError",
]

