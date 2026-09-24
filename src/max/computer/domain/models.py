"""Domain models for computer displays, windows, cursor, and screen captures."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.computer.domain.enums import PlatformType


class DisplayInfo(BaseModel):
    """Information representing a computer monitor / display device."""

    display_id: str = Field(..., description="Unique display identifier (e.g. 'display_0')")
    width: int = Field(..., description="Display horizontal resolution in pixels")
    height: int = Field(..., description="Display vertical resolution in pixels")
    x: int = Field(default=0, description="Virtual desktop top-left X coordinate")
    y: int = Field(default=0, description="Virtual desktop top-left Y coordinate")
    scale_factor: float = Field(default=1.0, description="DPI scaling ratio factor (e.g. 1.0, 1.25, 1.5)")
    primary: bool = Field(default=True, description="Whether this is the primary system monitor")
    orientation: int = Field(default=0, description="Screen rotation angle (0, 90, 180, 270)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class ScreenRegion(BaseModel):
    """Bounding box specifying a rectangular region of the screen."""

    x: int = Field(..., description="Top-left X coordinate")
    y: int = Field(..., description="Top-left Y coordinate")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")

    def is_valid(self) -> bool:
        """Check if region has non-zero positive dimensions."""
        return self.width > 0 and self.height > 0


class ScreenCapture(BaseModel):
    """Screen capture metadata and in-memory image reference."""

    capture_id: str = Field(
        default_factory=lambda: f"cap_{uuid.uuid4().hex[:12]}",
        description="Unique screen capture identifier",
    )
    display_id: str = Field(default="display_0", description="Associated display ID")
    region: ScreenRegion | None = Field(default=None, description="Captured screen region")
    width: int = Field(..., description="Captured image width in pixels")
    height: int = Field(..., description="Captured image height in pixels")
    image_reference: str | None = Field(default=None, description="In-memory base64 or buffer reference")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Capture timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Capture metadata attributes")


class CursorPosition(BaseModel):
    """Mouse pointer screen coordinates."""

    x: int = Field(..., description="Horizontal cursor position in pixels")
    y: int = Field(..., description="Vertical cursor position in pixels")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Observation timestamp"
    )


class WindowInfo(BaseModel):
    """Information describing a GUI application window."""

    window_id: str = Field(..., description="Unique window handle or ID string")
    title: str = Field(default="", description="Window title bar text")
    process_id: int | None = Field(default=None, description="Host process ID (PID) if available")
    application_identifier: str | None = Field(default=None, description="App name or executable name")
    x: int = Field(default=0, description="Window top-left X coordinate")
    y: int = Field(default=0, description="Window top-left Y coordinate")
    width: int = Field(default=800, description="Window width in pixels")
    height: int = Field(default=600, description="Window height in pixels")
    visible: bool = Field(default=True, description="Whether window is visible")
    minimized: bool = Field(default=False, description="Whether window is minimized")
    maximized: bool = Field(default=False, description="Whether window is maximized")
    focused: bool = Field(default=False, description="Whether window currently has foreground focus")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class InputDeviceState(BaseModel):
    """State snapshot of mouse and keyboard device parameters."""

    cursor_position: CursorPosition = Field(..., description="Current cursor position")
    active_modifiers: list[str] = Field(default_factory=list, description="Currently pressed modifier keys")
    mouse_pressed_buttons: list[str] = Field(default_factory=list, description="Currently held mouse buttons")


class ComputerState(BaseModel):
    """Unified operational state snapshot of the computer environment."""

    platform: PlatformType = Field(default=PlatformType.WINDOWS, description="Target OS platform")
    displays: list[DisplayInfo] = Field(default_factory=list, description="Available monitor displays")
    active_window: WindowInfo | None = Field(default=None, description="Currently focused foreground window")
    available_windows: list[WindowInfo] = Field(default_factory=list, description="Visible GUI windows")
    cursor_position: CursorPosition = Field(..., description="Current mouse cursor position")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Snapshot timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="System metadata attributes")


class ComputerTraceEvent(BaseModel):
    """Immutable operational trace log event for computer control auditing."""

    event_id: str = Field(
        default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}",
        description="Unique trace event identifier",
    )
    action_id: str | None = Field(default=None, description="Associated action ID if applicable")
    sequence_id: str | None = Field(default=None, description="Associated sequence ID if applicable")
    event_type: str = Field(..., description="Trace event type string (e.g. ACTION_STARTED)")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    details: dict[str, Any] = Field(default_factory=dict, description="Sanitized trace metadata")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )

