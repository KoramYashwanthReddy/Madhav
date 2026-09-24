"""Pydantic API response schemas for computer control REST API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.computer.domain.enums import (
    ComputerActionFailureReason,
    ComputerActionStatus,
    ComputerActionType,
)
from max.computer.domain.models import CursorPosition, DisplayInfo, ScreenCapture, WindowInfo


class ComputerStatusResponse(BaseModel):
    """System status response schema."""

    enabled: bool = Field(..., description="Whether real computer control is enabled")
    dry_run: bool = Field(..., description="Whether dry-run simulation mode is default")
    platform: str = Field(..., description="Target OS platform identifier")
    backend_type: str = Field(..., description="Class name of active backend")
    backend_available: bool = Field(..., description="Whether hardware control backend is available")
    screen_capture_enabled: bool = Field(..., description="Whether screen capture feature is enabled")


class DisplayResponse(BaseModel):
    """Display information response schema."""

    displays: list[DisplayInfo] = Field(..., description="List of connected monitors")


class CursorPositionResponse(BaseModel):
    """Cursor position response schema."""

    cursor: CursorPosition = Field(..., description="Current mouse pointer coordinates")


class ScreenCaptureResponse(BaseModel):
    """Screen capture response schema."""

    capture: ScreenCapture = Field(..., description="Screen capture metadata reference")


class WindowResponse(BaseModel):
    """Single window response schema."""

    window: WindowInfo | None = Field(default=None, description="Window details")


class WindowListResponse(BaseModel):
    """Window enumeration response schema."""

    windows: list[WindowInfo] = Field(..., description="List of open GUI windows")
    total: int = Field(..., description="Total window count")


class ComputerStateResponse(BaseModel):
    """Consolidated state snapshot response schema."""

    platform: str = Field(..., description="Target OS platform")
    displays: list[DisplayInfo] = Field(..., description="Displays")
    active_window: WindowInfo | None = Field(default=None, description="Active focused window")
    available_windows: list[WindowInfo] = Field(..., description="Visible windows")
    cursor_position: CursorPosition = Field(..., description="Cursor position")
    timestamp: datetime = Field(..., description="Snapshot timestamp")


class ComputerActionResultResponse(BaseModel):
    """Structured action result schema."""

    action_id: str = Field(..., description="Action ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    status: ComputerActionStatus = Field(..., description="Status")
    target: str | None = Field(default=None, description="Target")
    observed_state: dict[str, Any] = Field(default_factory=dict, description="Observed state payload")
    duration: float = Field(default=0.0, description="Duration seconds")
    timestamp: datetime = Field(..., description="Result timestamp")


class ComputerActionFailureResponse(BaseModel):
    """Structured action failure schema."""

    action_id: str = Field(..., description="Action ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    reason: ComputerActionFailureReason = Field(..., description="Normalized failure reason")
    message: str = Field(..., description="Failure explanation")
    details: dict[str, Any] = Field(default_factory=dict, description="Diagnostic details")
    timestamp: datetime = Field(..., description="Failure timestamp")


class ComputerActionResponse(BaseModel):
    """Unified computer action entity response schema."""

    action_id: str = Field(..., description="Action ID")
    action_type: ComputerActionType = Field(..., description="Action type")
    status: ComputerActionStatus = Field(..., description="Action lifecycle status")
    target: str | None = Field(default=None, description="Target identifier")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    agent_id: str | None = Field(default=None, description="Agent ID")
    permission_decision_id: str | None = Field(default=None, description="Authorization decision ID")
    result: ComputerActionResultResponse | None = Field(default=None, description="Result payload if completed")
    failure: ComputerActionFailureResponse | None = Field(default=None, description="Failure details if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class ActionSequenceResponse(BaseModel):
    """Action sequence response schema."""

    sequence_id: str = Field(..., description="Sequence ID")
    actions: list[ComputerActionResponse] = Field(..., description="Executed sequence actions")
    status: ComputerActionStatus = Field(..., description="Sequence status")
    stop_on_failure: bool = Field(..., description="Stop on failure flag")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
