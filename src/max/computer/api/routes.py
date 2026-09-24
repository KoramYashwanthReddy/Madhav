"""REST API router for Module 16 — Computer Control."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from max.computer.container import get_computer_container
from max.computer.domain.action import (
    ComputerAction,
    ComputerActionRequest,
    ComputerActionSequence,
)
from max.computer.domain.enums import ComputerActionStatus, ComputerActionType
from max.computer.schemas.requests import (
    ActionExecutionRequestSchema,
    KeyboardPressRequestSchema,
    KeyboardShortcutRequestSchema,
    KeyboardTypeRequestSchema,
    MouseClickRequestSchema,
    MouseDragRequestSchema,
    MouseMoveRequestSchema,
    MouseScrollRequestSchema,
    ScreenCaptureRequestSchema,
    SequenceExecutionRequestSchema,
    WindowMoveRequestSchema,
    WindowResizeRequestSchema,
)
from max.computer.schemas.responses import (
    ActionSequenceResponse,
    ComputerActionFailureResponse,
    ComputerActionResponse,
    ComputerActionResultResponse,
    ComputerStateResponse,
    ComputerStatusResponse,
    CursorPositionResponse,
    DisplayResponse,
    ScreenCaptureResponse,
    WindowListResponse,
    WindowResponse,
)
from max.computer.services.control_service import ComputerControlService

computer_router = APIRouter(prefix="/computer", tags=["Computer Control"])


def get_service() -> ComputerControlService:
    """Dependency provider for ComputerControlService."""
    return get_computer_container().control_service


def _format_action_response(action: ComputerAction) -> ComputerActionResponse:
    """Format domain ComputerAction to API response schema."""
    res_dto = None
    if action.result:
        res_dto = ComputerActionResultResponse(
            action_id=action.result.action_id,
            action_type=action.result.action_type,
            status=action.result.status,
            target=action.result.target,
            observed_state=action.result.observed_state,
            duration=action.result.duration,
            timestamp=action.result.timestamp,
        )
    fail_dto = None
    if action.failure:
        fail_dto = ComputerActionFailureResponse(
            action_id=action.failure.action_id,
            action_type=action.failure.action_type,
            reason=action.failure.reason,
            message=action.failure.message,
            details=action.failure.details,
            timestamp=action.failure.timestamp,
        )
    return ComputerActionResponse(
        action_id=action.action_id,
        action_type=action.request.action_type,
        status=action.status,
        target=action.request.target,
        parameters=action.request.parameters,
        agent_id=action.request.agent_id,
        permission_decision_id=action.request.permission_decision_id,
        result=res_dto,
        failure=fail_dto,
        created_at=action.created_at,
        updated_at=action.updated_at,
    )


# System & Observation Endpoints
@computer_router.get("/status", response_model=ComputerStatusResponse)
def get_computer_status(service: ComputerControlService = Depends(get_service)) -> ComputerStatusResponse:
    """Get system readiness and backend status."""
    st = service.get_status()
    return ComputerStatusResponse(**st)


@computer_router.get("/state", response_model=ComputerStateResponse)
def get_computer_state(service: ComputerControlService = Depends(get_service)) -> ComputerStateResponse:
    """Get consolidated snapshot of computer state."""
    state = service.get_computer_state()
    return ComputerStateResponse(
        platform=state.platform.value,
        displays=state.displays,
        active_window=state.active_window,
        available_windows=state.available_windows,
        cursor_position=state.cursor_position,
        timestamp=state.timestamp,
    )


@computer_router.get("/displays", response_model=DisplayResponse)
def get_displays(service: ComputerControlService = Depends(get_service)) -> DisplayResponse:
    """Get list of display monitors."""
    displays = service.get_displays()
    return DisplayResponse(displays=displays)


# Screen Endpoints
@computer_router.get("/screen/info", response_model=DisplayResponse)
def get_screen_info(service: ComputerControlService = Depends(get_service)) -> DisplayResponse:
    """Get display screen information."""
    displays = service.get_screen_info()
    return DisplayResponse(displays=displays)


@computer_router.post("/screen/capture", response_model=ScreenCaptureResponse)
def capture_screen(
    req: ScreenCaptureRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ScreenCaptureResponse:
    """Capture screen image."""
    cap = service.capture_screen(display_id=req.display_id, region=req.region)
    return ScreenCaptureResponse(capture=cap)


# Cursor Endpoints
@computer_router.get("/cursor", response_model=CursorPositionResponse)
def get_cursor_position(service: ComputerControlService = Depends(get_service)) -> CursorPositionResponse:
    """Get cursor position coordinates."""
    pos = service.get_cursor_position()
    return CursorPositionResponse(cursor=pos)


@computer_router.post("/cursor/move", response_model=ComputerActionResponse)
def move_cursor(
    req: MouseMoveRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Move cursor position."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.MOVE_MOUSE,
        parameters={"x": req.x, "y": req.y, "duration": req.duration},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


# Mouse Endpoints
@computer_router.post("/mouse/click", response_model=ComputerActionResponse)
def click_mouse(
    req: MouseClickRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Click mouse button."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.CLICK_MOUSE,
        parameters={"x": req.x, "y": req.y, "button": req.button.value, "click_count": req.click_count},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/mouse/double-click", response_model=ComputerActionResponse)
def double_click_mouse(
    req: MouseClickRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Double click mouse button."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.DOUBLE_CLICK_MOUSE,
        parameters={"x": req.x, "y": req.y, "button": req.button.value},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/mouse/drag", response_model=ComputerActionResponse)
def drag_mouse(
    req: MouseDragRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Drag mouse cursor."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.DRAG_MOUSE,
        parameters={
            "start_x": req.start_x,
            "start_y": req.start_y,
            "end_x": req.end_x,
            "end_y": req.end_y,
            "duration": req.duration,
            "button": req.button.value,
        },
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/mouse/scroll", response_model=ComputerActionResponse)
def scroll_mouse(
    req: MouseScrollRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Scroll mouse wheel."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.SCROLL_MOUSE,
        parameters={"clicks": req.clicks, "direction": req.direction, "x": req.x, "y": req.y},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


# Keyboard Endpoints
@computer_router.post("/keyboard/press", response_model=ComputerActionResponse)
def press_key(
    req: KeyboardPressRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Press keyboard key."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.PRESS_KEY,
        parameters={"key": req.key.value, "modifiers": [m.value for m in req.modifiers]},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/keyboard/type", response_model=ComputerActionResponse)
def type_text(
    req: KeyboardTypeRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Type text sequence."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.TYPE_TEXT,
        parameters={"text": req.text, "interval": req.interval},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/keyboard/shortcut", response_model=ComputerActionResponse)
def keyboard_shortcut(
    req: KeyboardShortcutRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Trigger keyboard shortcut combination."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.KEYBOARD_SHORTCUT,
        parameters={"keys": [k.value if hasattr(k, "value") else str(k) for k in req.keys]},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


# Window Endpoints
@computer_router.get("/windows", response_model=WindowListResponse)
def list_windows(
    visible_only: bool = Query(default=True),
    title_filter: str | None = Query(default=None),
    app_filter: str | None = Query(default=None),
    service: ComputerControlService = Depends(get_service),
) -> WindowListResponse:
    """List open GUI windows."""
    windows = service.list_windows(
        visible_only=visible_only, title_filter=title_filter, app_filter=app_filter
    )
    return WindowListResponse(windows=windows, total=len(windows))


@computer_router.get("/windows/active", response_model=WindowResponse)
def get_active_window(service: ComputerControlService = Depends(get_service)) -> WindowResponse:
    """Get active foreground focused window."""
    win = service.get_active_window()
    return WindowResponse(window=win)


@computer_router.post("/windows/{window_id}/focus", response_model=ComputerActionResponse)
def focus_window(
    window_id: str,
    permission_decision_id: str | None = Query(default=None),
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Focus target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.FOCUS_WINDOW,
        target=window_id,
        parameters={"window_id": window_id},
        permission_decision_id=permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/windows/{window_id}/minimize", response_model=ComputerActionResponse)
def minimize_window(
    window_id: str,
    permission_decision_id: str | None = Query(default=None),
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Minimize target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.MINIMIZE_WINDOW,
        target=window_id,
        parameters={"window_id": window_id},
        permission_decision_id=permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/windows/{window_id}/maximize", response_model=ComputerActionResponse)
def maximize_window(
    window_id: str,
    permission_decision_id: str | None = Query(default=None),
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Maximize target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.MAXIMIZE_WINDOW,
        target=window_id,
        parameters={"window_id": window_id},
        permission_decision_id=permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/windows/{window_id}/restore", response_model=ComputerActionResponse)
def restore_window(
    window_id: str,
    permission_decision_id: str | None = Query(default=None),
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Restore target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.RESTORE_WINDOW,
        target=window_id,
        parameters={"window_id": window_id},
        permission_decision_id=permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/windows/{window_id}/move", response_model=ComputerActionResponse)
def move_window(
    window_id: str,
    req: WindowMoveRequestSchema,
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Move target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.MOVE_WINDOW,
        target=window_id,
        parameters={"window_id": window_id, "x": req.x, "y": req.y},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


@computer_router.post("/windows/{window_id}/resize", response_model=ComputerActionResponse)
def resize_window(
    window_id: str,
    req: WindowResizeRequestSchema,
    service: ComputerControlService = Depends(get_service),
) -> ComputerActionResponse:
    """Resize target window."""
    action_req = ComputerActionRequest(
        action_type=ComputerActionType.RESIZE_WINDOW,
        target=window_id,
        parameters={"window_id": window_id, "width": req.width, "height": req.height},
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req)
    return _format_action_response(action)


# Action Management Endpoints
@computer_router.post("/actions", response_model=ComputerActionResponse)
def create_action(
    req: ActionExecutionRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Submit generic computer control action request."""
    action_req = ComputerActionRequest(
        action_type=req.action_type,
        target=req.target,
        parameters=req.parameters,
        agent_id=req.agent_id,
        agent_run_id=req.agent_run_id,
        task_id=req.task_id,
        plan_id=req.plan_id,
        conversation_id=req.conversation_id,
        owner_id=req.owner_id,
        permission_decision_id=req.permission_decision_id,
    )
    action = service.execute_action(action_req, dry_run=req.dry_run)
    return _format_action_response(action)


@computer_router.get("/actions", response_model=list[ComputerActionResponse])
def list_actions(
    status: ComputerActionStatus | None = Query(default=None),
    agent_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    service: ComputerControlService = Depends(get_service),
) -> list[ComputerActionResponse]:
    """List historical computer actions."""
    repo = get_computer_container().action_repo
    actions = repo.list_actions(status=status, agent_id=agent_id, limit=limit)
    return [_format_action_response(a) for a in actions]


@computer_router.get("/actions/{action_id}", response_model=ComputerActionResponse)
def get_action_by_id(
    action_id: str, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Get single computer action details by ID."""
    repo = get_computer_container().action_repo
    action = repo.get_by_id(action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action '{action_id}' not found")
    return _format_action_response(action)


@computer_router.post("/actions/{action_id}/cancel", response_model=ComputerActionResponse)
def cancel_action(
    action_id: str, service: ComputerControlService = Depends(get_service)
) -> ComputerActionResponse:
    """Cancel computer action."""
    action = service.cancel_action(action_id)
    return _format_action_response(action)


# Sequence Endpoints
@computer_router.post("/sequences", response_model=ActionSequenceResponse)
def create_sequence(
    req: SequenceExecutionRequestSchema, service: ComputerControlService = Depends(get_service)
) -> ActionSequenceResponse:
    """Submit action sequence execution."""
    action_reqs = [
        ComputerActionRequest(
            action_type=a.action_type,
            target=a.target,
            parameters=a.parameters,
            agent_id=a.agent_id,
            permission_decision_id=a.permission_decision_id,
        )
        for a in req.actions
    ]
    seq = ComputerActionSequence(actions=action_reqs, stop_on_failure=req.stop_on_failure)
    executed_seq = service.execute_sequence(seq, dry_run=req.dry_run)

    # Fetch stored actions
    repo = get_computer_container().action_repo
    action_dtos = []
    for a_req in executed_seq.actions:
        # Search repo by matching request parameters
        stored = repo.list_actions(limit=50)
        matched = next((a for a in stored if a.request.action_id == a_req.action_id), None)
        if matched:
            action_dtos.append(_format_action_response(matched))
        else:
            action_dtos.append(
                ComputerActionResponse(
                    action_id=a_req.action_id,
                    action_type=a_req.action_type,
                    status=executed_seq.status,
                    parameters=a_req.parameters,
                    created_at=executed_seq.created_at,
                    updated_at=executed_seq.created_at,
                )
            )

    return ActionSequenceResponse(
        sequence_id=executed_seq.sequence_id,
        actions=action_dtos,
        status=executed_seq.status,
        stop_on_failure=executed_seq.stop_on_failure,
        created_at=executed_seq.created_at,
        completed_at=executed_seq.completed_at,
    )
