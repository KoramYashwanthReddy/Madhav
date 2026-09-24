"""Unified ComputerControlService facade."""

import logging
from typing import Any

from max.computer.backends.base import ComputerControlBackend
from max.computer.backends.platform_detector import PlatformDetector
from max.computer.domain.action import (
    ComputerAction,
    ComputerActionRequest,
    ComputerActionSequence,
)
from max.computer.domain.models import (
    ComputerState,
    CursorPosition,
    DisplayInfo,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)
from max.computer.services.action_service import ComputerActionService
from max.computer.services.observation_service import ComputerObservationService
from max.config.settings import Settings
from max.security.domain.boundary import AuthorizedExecutionRequest

logger = logging.getLogger(__name__)


class ComputerControlService:
    """Unified application facade for computer observation, actions, and security gate execution."""

    def __init__(
        self,
        backend: ComputerControlBackend,
        observation_service: ComputerObservationService,
        action_service: ComputerActionService,
        settings: Settings,
    ) -> None:
        self._backend = backend
        self._obs_service = observation_service
        self._action_service = action_service
        self._settings = settings

    @property
    def backend(self) -> ComputerControlBackend:
        """Access underlying computer control backend interface."""
        return self._backend

    def get_status(self) -> dict[str, Any]:
        """Return system readiness, platform, backend type, and configuration flags."""
        platform = PlatformDetector.detect()
        available = self._backend.is_available()
        return {
            "enabled": self._settings.computer_control.enabled,
            "dry_run": self._settings.computer_control.dry_run,
            "platform": platform.value,
            "backend_type": type(self._backend).__name__,
            "backend_available": available,
            "screen_capture_enabled": self._settings.computer_control.screen_capture_enabled,
        }

    def get_computer_state(self) -> ComputerState:
        """Get snapshot of current computer environment."""
        return self._obs_service.get_computer_state()

    def get_displays(self) -> list[DisplayInfo]:
        """Get connected displays."""
        return self._obs_service.get_displays()

    def get_screen_info(self) -> list[DisplayInfo]:
        """Get display monitor information."""
        return self._obs_service.get_screen_info()

    def get_cursor_position(self) -> CursorPosition:
        """Get cursor position."""
        return self._obs_service.get_cursor_position()

    def capture_screen(
        self, display_id: str = "display_0", region: ScreenRegion | None = None
    ) -> ScreenCapture:
        """Capture screen image."""
        return self._obs_service.capture_screen(display_id=display_id, region=region)

    def get_active_window(self) -> WindowInfo | None:
        """Get focused window."""
        return self._obs_service.get_active_window()

    def list_windows(
        self,
        visible_only: bool = True,
        title_filter: str | None = None,
        app_filter: str | None = None,
    ) -> list[WindowInfo]:
        """List open windows."""
        return self._obs_service.list_windows(
            visible_only=visible_only, title_filter=title_filter, app_filter=app_filter
        )

    def execute_action(
        self,
        request: ComputerActionRequest,
        auth_token: AuthorizedExecutionRequest | None = None,
        dry_run: bool | None = None,
    ) -> ComputerAction:
        """Execute a single computer action."""
        return self._action_service.execute_action(
            request=request, auth_token=auth_token, dry_run=dry_run
        )

    def execute_sequence(
        self,
        sequence: ComputerActionSequence,
        auth_token: AuthorizedExecutionRequest | None = None,
        dry_run: bool | None = None,
    ) -> ComputerActionSequence:
        """Execute sequence of computer actions."""
        return self._action_service.execute_sequence(
            sequence=sequence, auth_token=auth_token, dry_run=dry_run
        )

    def cancel_action(self, action_id: str) -> ComputerAction:
        """Cancel computer action."""
        return self._action_service.cancel_action(action_id=action_id)
