"""Computer observation service for reading hardware/window state."""


from max.computer.backends.base import ComputerControlBackend
from max.computer.domain.models import (
    ComputerState,
    CursorPosition,
    DisplayInfo,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)


class ComputerObservationService:
    """Service providing read-only screen, display, cursor, and window observations."""

    def __init__(self, backend: ComputerControlBackend) -> None:
        self._backend = backend

    def get_displays(self) -> list[DisplayInfo]:
        """Get connected display monitors."""
        return self._backend.get_displays()

    def get_screen_info(self) -> list[DisplayInfo]:
        """Get display monitor information."""
        return self.get_displays()

    def get_cursor_position(self) -> CursorPosition:
        """Get current mouse cursor position."""
        return self._backend.get_cursor_position()

    def get_active_window(self) -> WindowInfo | None:
        """Get currently focused active window."""
        return self._backend.get_active_window()

    def list_windows(
        self,
        visible_only: bool = True,
        title_filter: str | None = None,
        app_filter: str | None = None,
    ) -> list[WindowInfo]:
        """List open windows with optional filtering."""
        windows = self._backend.list_windows()
        if visible_only:
            windows = [w for w in windows if w.visible]
        if title_filter:
            tf = title_filter.lower()
            windows = [w for w in windows if tf in w.title.lower()]
        if app_filter:
            af = app_filter.lower()
            windows = [
                w
                for w in windows
                if w.application_identifier and af in w.application_identifier.lower()
            ]
        return windows

    def capture_screen(
        self, display_id: str = "display_0", region: ScreenRegion | None = None
    ) -> ScreenCapture:
        """Capture screen image for given display and optional region."""
        return self._backend.capture_screen(display_id=display_id, region=region)

    def get_computer_state(self) -> ComputerState:
        """Get consolidated current snapshot of computer environment."""
        displays = self.get_displays()
        cursor = self.get_cursor_position()
        active_window = self.get_active_window()
        windows = self.list_windows(visible_only=True)
        return ComputerState(
            displays=displays,
            active_window=active_window,
            available_windows=windows,
            cursor_position=cursor,
        )
