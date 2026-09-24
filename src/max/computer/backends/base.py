"""Abstract base class interface for ComputerControlBackend implementations."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from max.computer.domain.enums import KeyboardKey, KeyboardModifier, MouseButton, PlatformType
from max.computer.domain.models import (
    CursorPosition,
    DisplayInfo,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)


class ComputerControlBackend(ABC):
    """Abstract interface defining low-level OS computer control operations."""

    @property
    @abstractmethod
    def platform(self) -> PlatformType:
        """Return operating system platform type."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend dependencies and OS APIs are operational."""
        pass

    # --- Screen / Display Operations ---

    @abstractmethod
    def get_displays(self) -> list[DisplayInfo]:
        """Get list of active monitors/displays."""
        pass

    @abstractmethod
    def capture_screen(
        self, display_id: str = "display_0", region: ScreenRegion | None = None
    ) -> ScreenCapture:
        """Capture screenshot of screen or specified region."""
        pass

    # --- Cursor / Mouse Operations ---

    @abstractmethod
    def get_cursor_position(self) -> CursorPosition:
        """Get current mouse cursor screen coordinates."""
        pass

    @abstractmethod
    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> CursorPosition:
        """Move cursor to target (x, y) coordinates."""
        pass

    @abstractmethod
    def click_mouse(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = MouseButton.LEFT,
        click_count: int = 1,
    ) -> CursorPosition:
        """Click mouse button at current or specified position."""
        pass

    @abstractmethod
    def double_click_mouse(
        self, x: int | None = None, y: int | None = None, button: MouseButton = MouseButton.LEFT
    ) -> CursorPosition:
        """Double click mouse button."""
        pass

    @abstractmethod
    def drag_mouse(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ) -> CursorPosition:
        """Perform click-and-drag mouse operation."""
        pass

    @abstractmethod
    def scroll_mouse(
        self,
        clicks: int,
        direction: str = "vertical",
        x: int | None = None,
        y: int | None = None,
    ) -> bool:
        """Scroll mouse wheel."""
        pass

    # --- Keyboard Operations ---

    @abstractmethod
    def press_key(
        self, key: KeyboardKey | str, modifiers: Sequence[KeyboardModifier | str] | None = None
    ) -> bool:
        """Press and release a single keyboard key."""
        pass

    @abstractmethod
    def type_text(self, text: str, interval: float = 0.0) -> bool:
        """Type a sequence of characters."""
        pass

    @abstractmethod
    def keyboard_shortcut(self, keys: Sequence[KeyboardKey | str]) -> bool:
        """Trigger a key combination shortcut (e.g. ['CTRL', 'C'])."""
        pass

    # --- Window Operations ---

    @abstractmethod
    def get_active_window(self) -> WindowInfo | None:
        """Get currently focused foreground window."""
        pass

    @abstractmethod
    def list_windows(self, visible_only: bool = True) -> list[WindowInfo]:
        """List open GUI application windows."""
        pass

    @abstractmethod
    def focus_window(self, window_id: str) -> WindowInfo | None:
        """Bring target window to foreground focus."""
        pass

    @abstractmethod
    def minimize_window(self, window_id: str) -> WindowInfo | None:
        """Minimize target window."""
        pass

    @abstractmethod
    def maximize_window(self, window_id: str) -> WindowInfo | None:
        """Maximize target window."""
        pass

    @abstractmethod
    def restore_window(self, window_id: str) -> WindowInfo | None:
        """Restore target window to normal bounds."""
        pass

    @abstractmethod
    def move_window(self, window_id: str, x: int, y: int) -> WindowInfo | None:
        """Move target window to new (x, y) coordinates."""
        pass

    @abstractmethod
    def resize_window(self, window_id: str, width: int, height: int) -> WindowInfo | None:
        """Resize target window dimensions."""
        pass
