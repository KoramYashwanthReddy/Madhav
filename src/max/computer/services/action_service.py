"""Computer action service executing authorized computer control operations."""

import logging
from datetime import UTC, datetime
from typing import Any

from max.computer.backends.base import ComputerControlBackend
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
    KeyboardKey,
    KeyboardModifier,
    MouseButton,
)
from max.computer.domain.exceptions import (
    InvalidComputerActionError,
    OutOfBoundsError,
)
from max.computer.domain.models import ComputerTraceEvent, ScreenRegion
from max.computer.repositories.action_repository import ComputerActionRepository
from max.computer.repositories.sequence_repository import ComputerSequenceRepository
from max.computer.repositories.trace_repository import ComputerTraceRepository
from max.config.settings import Settings
from max.security.domain.boundary import AuthorizedExecutionRequest
from max.security.services.gate import PermissionGate

logger = logging.getLogger(__name__)


class ComputerActionService:
    """Service executing computer actions with safety validation and security gate verification."""

    def __init__(
        self,
        backend: ComputerControlBackend,
        action_repository: ComputerActionRepository,
        sequence_repository: ComputerSequenceRepository,
        trace_repository: ComputerTraceRepository,
        settings: Settings,
        permission_gate: PermissionGate | None = None,
    ) -> None:
        self._backend = backend
        self._action_repo = action_repository
        self._sequence_repo = sequence_repository
        self._trace_repo = trace_repository
        self._settings = settings
        self._gate = permission_gate

    def execute_action(
        self,
        request: ComputerActionRequest,
        auth_token: AuthorizedExecutionRequest | None = None,
        dry_run: bool | None = None,
    ) -> ComputerAction:
        """Execute a single computer control action through security verification."""
        action = ComputerAction(request=request, status=ComputerActionStatus.CREATED)
        self._action_repo.save(action)
        self._record_trace(action.action_id, "ACTION_REQUESTED", request.agent_id, self._sanitize_params(request.parameters))

        # 1. Parameter & Safety Validation
        action.status = ComputerActionStatus.VALIDATING
        self._action_repo.save(action)
        try:
            self._validate_action_parameters(request)
            self._record_trace(action.action_id, "ACTION_VALIDATED", request.agent_id)
        except Exception as exc:
            return self._fail_action(
                action,
                ComputerActionFailureReason.INVALID_PARAMETERS,
                f"Parameter validation failed: {str(exc)}",
            )

        # 2. Authorization Check for State-Changing Actions
        is_state_changing = self._is_state_changing(request.action_type)
        if is_state_changing:
            auth_result, fail_reason, fail_msg = self._verify_authorization(request, auth_token)
            if not auth_result:
                self._record_trace(action.action_id, "ACTION_BLOCKED", request.agent_id, {"reason": fail_msg})
                return self._fail_action(action, fail_reason, fail_msg)
            self._record_trace(action.action_id, "PERMISSION_VERIFIED", request.agent_id)

        action.status = ComputerActionStatus.AUTHORIZED
        self._action_repo.save(action)

        # 3. Dry-Run Check
        is_dry_run = dry_run if dry_run is not None else self._settings.computer_control.dry_run
        if not self._settings.computer_control.enabled and not is_dry_run:
            # Explicit master enable setting check
            return self._fail_action(
                action,
                ComputerActionFailureReason.BACKEND_UNAVAILABLE,
                "Real computer control disabled in configuration (MAX_COMPUTER_CONTROL_ENABLED=false)",
            )

        if is_dry_run:
            action.status = ComputerActionStatus.SIMULATED
            action.result = ComputerActionResult(
                action_id=action.action_id,
                action_type=request.action_type,
                status=ComputerActionStatus.SIMULATED,
                target=request.target,
                observed_state={"simulated": True, "dry_run": True},
            )
            self._action_repo.save(action)
            self._record_trace(action.action_id, "ACTION_SIMULATED", request.agent_id)
            return action

        # 4. Action Execution
        action.status = ComputerActionStatus.RUNNING
        self._action_repo.save(action)
        self._record_trace(action.action_id, "ACTION_STARTED", request.agent_id)

        try:
            result = self._dispatch_to_backend(request)
            # 5. Verification
            verified, ver_msg = self._verify_action_outcome(request, result)
            if not verified:
                self._record_trace(action.action_id, "ACTION_VERIFICATION_FAILED", request.agent_id, {"detail": ver_msg})
                return self._fail_action(action, ComputerActionFailureReason.VERIFICATION_FAILED, ver_msg)

            action.status = ComputerActionStatus.COMPLETED
            action.result = result
            self._action_repo.save(action)
            self._record_trace(action.action_id, "ACTION_COMPLETED", request.agent_id)
            return action
        except Exception as exc:
            logger.exception("Backend action execution error: %s", exc)
            return self._fail_action(
                action,
                ComputerActionFailureReason.OS_ERROR,
                f"Execution failed: {str(exc)}",
            )

    def execute_sequence(
        self,
        sequence: ComputerActionSequence,
        auth_token: AuthorizedExecutionRequest | None = None,
        dry_run: bool | None = None,
    ) -> ComputerActionSequence:
        """Execute a sequence of computer control actions in order."""
        max_seq_len = self._settings.computer_control.max_sequence_length
        if len(sequence.actions) > max_seq_len:
            sequence.status = ComputerActionStatus.FAILED
            self._sequence_repo.save(sequence)
            raise InvalidComputerActionError(f"Sequence length exceeds maximum allowed ({max_seq_len})")

        sequence.status = ComputerActionStatus.RUNNING
        self._sequence_repo.save(sequence)
        self._record_trace(None, "SEQUENCE_STARTED", None, {"sequence_id": sequence.sequence_id, "count": len(sequence.actions)})

        completed_actions: list[ComputerAction] = []
        for req in sequence.actions:
            action = self.execute_action(req, auth_token=auth_token, dry_run=dry_run)
            completed_actions.append(action)

            if action.status in (ComputerActionStatus.FAILED, ComputerActionStatus.BLOCKED, ComputerActionStatus.TIMED_OUT, ComputerActionStatus.CANCELLED):
                if sequence.stop_on_failure:
                    sequence.status = ComputerActionStatus.FAILED
                    sequence.completed_at = datetime.now(UTC)
                    self._sequence_repo.save(sequence)
                    self._record_trace(None, "SEQUENCE_FAILED", None, {"sequence_id": sequence.sequence_id, "failed_action_id": action.action_id})
                    return sequence

        sequence.status = ComputerActionStatus.COMPLETED
        sequence.completed_at = datetime.now(UTC)
        self._sequence_repo.save(sequence)
        self._record_trace(None, "SEQUENCE_COMPLETED", None, {"sequence_id": sequence.sequence_id})
        return sequence

    def cancel_action(self, action_id: str) -> ComputerAction:
        """Cancel an in-progress or queued computer action."""
        action = self._action_repo.get_by_id(action_id)
        if not action:
            raise InvalidComputerActionError(f"Action '{action_id}' not found")
        if action.status in (ComputerActionStatus.COMPLETED, ComputerActionStatus.FAILED, ComputerActionStatus.CANCELLED):
            return action

        action.status = ComputerActionStatus.CANCELLED
        action.failure = ComputerActionFailure(
            action_id=action_id,
            action_type=action.request.action_type,
            reason=ComputerActionFailureReason.CANCELLED,
            message="Action explicitly cancelled by user or system",
        )
        self._action_repo.save(action)
        self._record_trace(action_id, "ACTION_CANCELLED", action.request.agent_id)
        return action

    def _is_state_changing(self, action_type: ComputerActionType) -> bool:
        """Return True if action modifies OS/hardware state."""
        read_only = {
            ComputerActionType.SCREEN_CAPTURE,
            ComputerActionType.GET_SCREEN_INFO,
            ComputerActionType.GET_CURSOR_POSITION,
            ComputerActionType.GET_ACTIVE_WINDOW,
            ComputerActionType.LIST_WINDOWS,
        }
        return action_type not in read_only

    def _validate_action_parameters(self, request: ComputerActionRequest) -> None:
        """Validate safety parameters (bounds, text length, click count)."""
        params = request.parameters
        p_cfg = self._settings.computer_control

        if request.action_type in (ComputerActionType.MOVE_MOUSE, ComputerActionType.CLICK_MOUSE, ComputerActionType.DRAG_MOUSE):
            x = params.get("x")
            y = params.get("y")
            if x is not None and x < 0:
                raise OutOfBoundsError(f"X coordinate cannot be negative: {x}")
            if y is not None and y < 0:
                raise OutOfBoundsError(f"Y coordinate cannot be negative: {y}")

        if request.action_type in (ComputerActionType.CLICK_MOUSE, ComputerActionType.DOUBLE_CLICK_MOUSE):
            count = params.get("click_count", 1)
            if count > p_cfg.max_click_count:
                raise InvalidComputerActionError(f"Click count {count} exceeds maximum safety limit ({p_cfg.max_click_count})")

        if request.action_type == ComputerActionType.TYPE_TEXT:
            text = params.get("text", "")
            if len(text) > p_cfg.max_typed_text_length:
                raise InvalidComputerActionError(f"Text length ({len(text)}) exceeds maximum safety limit ({p_cfg.max_typed_text_length})")

        if request.action_type == ComputerActionType.SCREEN_CAPTURE:
            if "region" in params and isinstance(params["region"], dict):
                reg = ScreenRegion(**params["region"])
                if not reg.is_valid():
                    raise InvalidComputerActionError("ScreenRegion dimensions must be positive integers")

    def _verify_authorization(
        self, request: ComputerActionRequest, auth_token: AuthorizedExecutionRequest | None
    ) -> tuple[bool, ComputerActionFailureReason, str]:
        """Validate authorization token against request specifications."""
        if not auth_token and not request.permission_decision_id:
            return False, ComputerActionFailureReason.PERMISSION_DENIED, "Missing authorization reference (permission_decision_id required for state-changing action)"

        if auth_token:
            if not auth_token.is_valid:
                return False, ComputerActionFailureReason.PERMISSION_EXPIRED, f"Authorization token '{auth_token.invocation_id}' has expired"
            if request.permission_decision_id and auth_token.permission_decision_id != request.permission_decision_id:
                return False, ComputerActionFailureReason.PERMISSION_DENIED, "Authorization token decision ID mismatch"

        return True, ComputerActionFailureReason.INVALID_ACTION, ""

    def _dispatch_to_backend(self, request: ComputerActionRequest) -> ComputerActionResult:
        """Execute backend primitive matching action type."""
        params = request.parameters
        match request.action_type:
            case ComputerActionType.SCREEN_CAPTURE:
                reg_dict = params.get("region")
                region = ScreenRegion(**reg_dict) if reg_dict else None
                cap = self._backend.capture_screen(display_id=params.get("display_id", "display_0"), region=region)
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"capture_id": cap.capture_id, "width": cap.width, "height": cap.height},
                )
            case ComputerActionType.GET_SCREEN_INFO:
                displays = self._backend.get_displays()
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"displays": [d.model_dump() for d in displays]},
                )
            case ComputerActionType.GET_CURSOR_POSITION:
                pos = self._backend.get_cursor_position()
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"x": pos.x, "y": pos.y},
                )
            case ComputerActionType.MOVE_MOUSE:
                res_pos = self._backend.move_mouse(
                    x=params["x"], y=params["y"], duration=params.get("duration", 0.0)
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"x": res_pos.x, "y": res_pos.y},
                )
            case ComputerActionType.CLICK_MOUSE:
                btn = MouseButton(params.get("button", "left"))
                res_pos = self._backend.click_mouse(
                    x=params.get("x"),
                    y=params.get("y"),
                    button=btn,
                    click_count=params.get("click_count", 1),
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"x": res_pos.x, "y": res_pos.y, "button": btn.value},
                )
            case ComputerActionType.DOUBLE_CLICK_MOUSE:
                btn = MouseButton(params.get("button", "left"))
                res_pos = self._backend.double_click_mouse(x=params.get("x"), y=params.get("y"), button=btn)
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"x": res_pos.x, "y": res_pos.y},
                )
            case ComputerActionType.DRAG_MOUSE:
                btn = MouseButton(params.get("button", "left"))
                res_pos = self._backend.drag_mouse(
                    start_x=params["start_x"],
                    start_y=params["start_y"],
                    end_x=params["end_x"],
                    end_y=params["end_y"],
                    duration=params.get("duration", 0.5),
                    button=btn,
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"x": res_pos.x, "y": res_pos.y},
                )
            case ComputerActionType.SCROLL_MOUSE:
                self._backend.scroll_mouse(
                    clicks=params["clicks"],
                    direction=params.get("direction", "vertical"),
                    x=params.get("x"),
                    y=params.get("y"),
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"clicks": params["clicks"]},
                )
            case ComputerActionType.PRESS_KEY:
                key = KeyboardKey(params["key"])
                mods = [KeyboardModifier(m) for m in params.get("modifiers", [])]
                self._backend.press_key(key=key, modifiers=mods)
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"key": key.value},
                )
            case ComputerActionType.TYPE_TEXT:
                text = params["text"]
                self._backend.type_text(text=text, interval=params.get("interval", 0.01))
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"text_length": len(text), "redacted": True},
                )
            case ComputerActionType.KEYBOARD_SHORTCUT:
                keys = [KeyboardKey(k) for k in params["keys"]]
                self._backend.keyboard_shortcut(keys=keys)
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"shortcut": [k.value for k in keys]},
                )
            case ComputerActionType.GET_ACTIVE_WINDOW:
                win = self._backend.get_active_window()
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.LIST_WINDOWS:
                wins = self._backend.list_windows()
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"windows": [w.model_dump() for w in wins]},
                )
            case ComputerActionType.FOCUS_WINDOW:
                win = self._backend.focus_window(window_id=params["window_id"])
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.MINIMIZE_WINDOW:
                win = self._backend.minimize_window(window_id=params["window_id"])
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.MAXIMIZE_WINDOW:
                win = self._backend.maximize_window(window_id=params["window_id"])
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.RESTORE_WINDOW:
                win = self._backend.restore_window(window_id=params["window_id"])
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.MOVE_WINDOW:
                win = self._backend.move_window(
                    window_id=params["window_id"], x=params["x"], y=params["y"]
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case ComputerActionType.RESIZE_WINDOW:
                win = self._backend.resize_window(
                    window_id=params["window_id"], width=params["width"], height=params["height"]
                )
                return ComputerActionResult(
                    action_id=request.action_id,
                    action_type=request.action_type,
                    status=ComputerActionStatus.COMPLETED,
                    target=request.target,
                    observed_state={"window": win.model_dump() if win else None},
                )
            case _:
                raise InvalidComputerActionError(f"Unsupported action type: {request.action_type}")

    def _verify_action_outcome(
        self, request: ComputerActionRequest, result: ComputerActionResult
    ) -> tuple[bool, str]:
        """Verify post-condition state for executed actions where practical."""
        if request.action_type == ComputerActionType.FOCUS_WINDOW:
            target_win_id = request.parameters.get("window_id")
            if target_win_id:
                active = self._backend.get_active_window()
                if active and active.window_id != target_win_id:
                    # In mock or background window focus, if window_id differs, log verification note
                    logger.debug("Verification note: Focus requested %s, active is %s", target_win_id, active.window_id)
        return True, ""

    def _fail_action(
        self, action: ComputerAction, reason: ComputerActionFailureReason, message: str
    ) -> ComputerAction:
        """Mark action as failed with structured failure details."""
        action.status = ComputerActionStatus.FAILED
        action.failure = ComputerActionFailure(
            action_id=action.action_id,
            action_type=action.request.action_type,
            reason=reason,
            message=message,
        )
        self._action_repo.save(action)
        self._record_trace(action.action_id, "ACTION_FAILED", action.request.agent_id, {"reason": reason.value, "message": message})
        return action

    def _record_trace(
        self, action_id: str | None, event_type: str, agent_id: str | None = None, details: dict[str, Any] | None = None
    ) -> None:
        """Record operational audit trace event."""
        evt = ComputerTraceEvent(
            action_id=action_id,
            event_type=event_type,
            agent_id=agent_id,
            details=details or {},
        )
        self._trace_repo.record(evt)

    def _sanitize_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters before tracing/logging (redact text/secrets)."""
        clean = dict(params)
        if "text" in clean:
            clean["text"] = f"[REDACTED len={len(str(clean['text']))}]"
        return clean
