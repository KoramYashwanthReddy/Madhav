"""Enumerations for Module 16 — Computer Control."""

from enum import StrEnum
from typing import Any


class _CaseInsensitiveStrEnum(StrEnum):
    """Base StrEnum performing case-insensitive value matching."""

    @classmethod
    def _missing_(cls, value: object) -> Any:
        if isinstance(value, str):
            val_upper = value.upper()
            for member in cls:
                if member.value.upper() == val_upper:
                    return member
        return None


class ComputerActionType(_CaseInsensitiveStrEnum):
    """Explicit computer action operations."""

    SCREEN_CAPTURE = "SCREEN_CAPTURE"
    GET_SCREEN_INFO = "GET_SCREEN_INFO"
    GET_CURSOR_POSITION = "GET_CURSOR_POSITION"
    MOVE_MOUSE = "MOVE_MOUSE"
    CLICK_MOUSE = "CLICK_MOUSE"
    DOUBLE_CLICK_MOUSE = "DOUBLE_CLICK_MOUSE"
    DRAG_MOUSE = "DRAG_MOUSE"
    SCROLL_MOUSE = "SCROLL_MOUSE"
    PRESS_KEY = "PRESS_KEY"
    TYPE_TEXT = "TYPE_TEXT"
    KEYBOARD_SHORTCUT = "KEYBOARD_SHORTCUT"
    GET_ACTIVE_WINDOW = "GET_ACTIVE_WINDOW"
    LIST_WINDOWS = "LIST_WINDOWS"
    FOCUS_WINDOW = "FOCUS_WINDOW"
    MINIMIZE_WINDOW = "MINIMIZE_WINDOW"
    MAXIMIZE_WINDOW = "MAXIMIZE_WINDOW"
    RESTORE_WINDOW = "RESTORE_WINDOW"
    MOVE_WINDOW = "MOVE_WINDOW"
    RESIZE_WINDOW = "RESIZE_WINDOW"


class ComputerActionStatus(_CaseInsensitiveStrEnum):
    """Lifecycle status of a computer control action."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED = "BLOCKED"
    SIMULATED = "SIMULATED"


class ComputerActionFailureReason(_CaseInsensitiveStrEnum):
    """Structured failure categorization."""

    INVALID_ACTION = "INVALID_ACTION"
    INVALID_TARGET = "INVALID_TARGET"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PERMISSION_EXPIRED = "PERMISSION_EXPIRED"
    SECURITY_BLOCKED = "SECURITY_BLOCKED"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    OS_ERROR = "OS_ERROR"
    WINDOW_NOT_FOUND = "WINDOW_NOT_FOUND"
    DISPLAY_NOT_FOUND = "DISPLAY_NOT_FOUND"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class MouseButton(_CaseInsensitiveStrEnum):
    """Mouse buttons."""

    LEFT = "LEFT"
    RIGHT = "RIGHT"
    MIDDLE = "MIDDLE"


class KeyboardKey(_CaseInsensitiveStrEnum):
    """Supported keyboard keys."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"  # noqa: E741
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"  # noqa: E741
    P = "P"
    Q = "Q"
    R = "R"
    S = "S"
    T = "T"
    U = "U"
    V = "V"
    W = "W"
    X = "X"
    Y = "Y"
    Z = "Z"
    ENTER = "ENTER"
    ESC = "ESC"
    TAB = "TAB"
    BACKSPACE = "BACKSPACE"
    SPACE = "SPACE"
    DELETE = "DELETE"
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    HOME = "HOME"
    END = "END"
    PAGE_UP = "PAGE_UP"
    PAGE_DOWN = "PAGE_DOWN"
    CAPS_LOCK = "CAPS_LOCK"
    NUM_LOCK = "NUM_LOCK"
    PRINTSCREEN = "PRINTSCREEN"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"
    F6 = "F6"
    F7 = "F7"
    F8 = "F8"
    F9 = "F9"
    F10 = "F10"
    F11 = "F11"
    F12 = "F12"


class KeyboardModifier(_CaseInsensitiveStrEnum):
    """Keyboard modifier keys."""

    CTRL = "CTRL"
    ALT = "ALT"
    SHIFT = "SHIFT"
    WIN = "WIN"


class ComputerCapability(_CaseInsensitiveStrEnum):
    """Computer control capability classification."""

    SCREEN_READ = "SCREEN_READ"
    MOUSE_CONTROL = "MOUSE_CONTROL"
    KEYBOARD_CONTROL = "KEYBOARD_CONTROL"
    WINDOW_READ = "WINDOW_READ"
    WINDOW_CONTROL = "WINDOW_CONTROL"
    DISPLAY_READ = "DISPLAY_READ"


class PlatformType(_CaseInsensitiveStrEnum):
    """Operating system platform identifier."""

    WINDOWS = "WINDOWS"
    LINUX = "LINUX"
    MACOS = "MACOS"
    UNKNOWN = "UNKNOWN"
