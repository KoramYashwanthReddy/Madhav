"""Pydantic API request schemas for computer control REST API endpoints."""

from typing import Any

from pydantic import BaseModel, Field

from max.computer.domain.enums import ComputerActionType, KeyboardKey, KeyboardModifier, MouseButton
from max.computer.domain.models import ScreenRegion


class ScreenCaptureRequestSchema(BaseModel):
    """API request body for screen capture."""

    display_id: str = Field(default="display_0", description="Display monitor ID")
    region: ScreenRegion | None = Field(default=None, description="Optional bounding box region")


class MouseMoveRequestSchema(BaseModel):
    """API request body for moving mouse cursor."""

    x: int = Field(..., ge=0, description="Target X coordinate")
    y: int = Field(..., ge=0, description="Target Y coordinate")
    duration: float = Field(default=0.0, ge=0.0, le=10.0, description="Movement duration seconds")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class MouseClickRequestSchema(BaseModel):
    """API request body for clicking mouse button."""

    x: int | None = Field(default=None, ge=0, description="Optional target X coordinate")
    y: int | None = Field(default=None, ge=0, description="Optional target Y coordinate")
    button: MouseButton = Field(default=MouseButton.LEFT, description="Mouse button")
    click_count: int = Field(default=1, ge=1, le=10, description="Click count")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class MouseDragRequestSchema(BaseModel):
    """API request body for mouse click-and-drag."""

    start_x: int = Field(..., ge=0, description="Start X coordinate")
    start_y: int = Field(..., ge=0, description="Start Y coordinate")
    end_x: int = Field(..., ge=0, description="End X coordinate")
    end_y: int = Field(..., ge=0, description="End Y coordinate")
    duration: float = Field(default=0.5, ge=0.0, le=10.0, description="Drag duration seconds")
    button: MouseButton = Field(default=MouseButton.LEFT, description="Mouse button")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class MouseScrollRequestSchema(BaseModel):
    """API request body for scrolling mouse wheel."""

    clicks: int = Field(..., description="Scroll amount/clicks")
    direction: str = Field(default="vertical", description="Scroll direction ('vertical', 'horizontal')")
    x: int | None = Field(default=None, ge=0, description="Optional X pointer coordinate")
    y: int | None = Field(default=None, ge=0, description="Optional Y pointer coordinate")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class KeyboardPressRequestSchema(BaseModel):
    """API request body for pressing a single key."""

    key: KeyboardKey = Field(..., description="Target keyboard key")
    modifiers: list[KeyboardModifier] = Field(default_factory=list, description="Key modifiers")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class KeyboardTypeRequestSchema(BaseModel):
    """API request body for typing text."""

    text: str = Field(..., max_length=1000, description="Text string to type")
    interval: float = Field(default=0.01, ge=0.0, le=1.0, description="Inter-character typing interval seconds")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class KeyboardShortcutRequestSchema(BaseModel):
    """API request body for triggering keyboard shortcut."""

    keys: list[str] = Field(..., min_length=1, max_length=6, description="Key combination array")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class WindowMoveRequestSchema(BaseModel):
    """API request body for moving a window."""

    x: int = Field(..., description="New X coordinate")
    y: int = Field(..., description="New Y coordinate")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class WindowResizeRequestSchema(BaseModel):
    """API request body for resizing a window."""

    width: int = Field(..., ge=1, description="New width in pixels")
    height: int = Field(..., ge=1, description="New height in pixels")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")


class ActionExecutionRequestSchema(BaseModel):
    """Generic API request body for creating a computer action."""

    action_type: ComputerActionType = Field(..., description="Computer action type string")
    target: str | None = Field(default=None, description="Action target identifier")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters dictionary")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    agent_run_id: str | None = Field(default=None, description="Agent run ID")
    task_id: str | None = Field(default=None, description="Task ID")
    plan_id: str | None = Field(default=None, description="Plan ID")
    conversation_id: str | None = Field(default=None, description="Conversation ID")
    owner_id: str = Field(default="user", description="Owner ID")
    permission_decision_id: str | None = Field(default=None, description="Module 15 authorization decision ID")
    dry_run: bool | None = Field(default=None, description="Optional dry-run execution override")


class SequenceExecutionRequestSchema(BaseModel):
    """API request body for executing an action sequence."""

    actions: list[ActionExecutionRequestSchema] = Field(..., min_length=1, max_length=50, description="List of actions")
    stop_on_failure: bool = Field(default=True, description="Stop sequence execution on action failure")
    dry_run: bool | None = Field(default=None, description="Optional dry-run execution override")
