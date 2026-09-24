"""Mock computer control backend implementation for testing and dry-run simulation."""

import threading
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from max.computer.backends.base import ComputerControlBackend
from max.computer.domain.enums import KeyboardKey, KeyboardModifier, MouseButton, PlatformType
from max.computer.domain.exceptions import WindowNotFoundError
from max.computer.domain.models import (
    CursorPosition,
    DisplayInfo,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)


class MockComputerControlBackend(ComputerControlBackend):
    """Deterministic in-memory mock backend simulating computer interaction."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._platform = PlatformType.WINDOWS
        self._cursor = CursorPosition(x=100, y=100)
        self._displays = [
            DisplayInfo(
                display_id="display_0",
                width=1920,
                height=1080,
                x=0,
                y=0,
                scale_factor=1.0,
                primary=True,
            )
        ]
        self._windows = {
            "win_main": WindowInfo(
                window_id="win_main",
                title="Max Test Application Window",
                process_id=1234,
                application_identifier="max_test_app.exe",
                x=50,
                y=50,
                width=800,
                height=600,
                visible=True,
                focused=True,
            ),
            "win_secondary": WindowInfo(
                window_id="win_secondary",
                title="Browser - Max AI",
                process_id=5678,
                application_identifier="browser.exe",
                x=200,
                y=200,
                width=1280,
                height=720,
                visible=True,
                focused=False,
            ),
        }
        self.recorded_actions: list[dict[str, Any]] = []

    @property
    def platform(self) -> PlatformType:
        return self._platform

    def is_available(self) -> bool:
        return True

    def get_displays(self) -> list[DisplayInfo]:
        with self._lock:
            return list(self._displays)

    def capture_screen(
        self, display_id: str = "display_0", region: ScreenRegion | None = None
    ) -> ScreenCapture:
        with self._lock:
            w = region.width if region else 1920
            h = region.height if region else 1080
            return ScreenCapture(
                display_id=display_id,
                region=region,
                width=w,
                height=h,
                image_reference="mock_base64_image_data_buffer",
                timestamp=datetime.now(UTC),
            )

    def get_cursor_position(self) -> CursorPosition:
        with self._lock:
            return self._cursor

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> CursorPosition:
        with self._lock:
            self._cursor = CursorPosition(x=x, y=y, timestamp=datetime.now(UTC))
            self.recorded_actions.append({"action": "MOVE_MOUSE", "x": x, "y": y})
            return self._cursor

    def click_mouse(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = MouseButton.LEFT,
        click_count: int = 1,
    ) -> CursorPosition:
        with self._lock:
            if x is not None and y is not None:
                self._cursor = CursorPosition(x=x, y=y, timestamp=datetime.now(UTC))
            self.recorded_actions.append(
                {"action": "CLICK_MOUSE", "x": self._cursor.x, "y": self._cursor.y, "button": button.value, "count": click_count}
            )
            return self._cursor

    def double_click_mouse(
        self, x: int | None = None, y: int | None = None, button: MouseButton = MouseButton.LEFT
    ) -> CursorPosition:
        return self.click_mouse(x=x, y=y, button=button, click_count=2)

    def drag_mouse(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5,
        button: MouseButton = MouseButton.LEFT,
    ) -> CursorPosition:
        with self._lock:
            self.move_mouse(start_x, start_y)
            self.move_mouse(end_x, end_y)
            self.recorded_actions.append(
                {"action": "DRAG_MOUSE", "start_x": start_x, "start_y": start_y, "end_x": end_x, "end_y": end_y}
            )
            return self._cursor

    def scroll_mouse(
        self,
        clicks: int,
        direction: str = "vertical",
        x: int | None = None,
        y: int | None = None,
    ) -> bool:
        with self._lock:
            if x is not None and y is not None:
                self.move_mouse(x, y)
            self.recorded_actions.append({"action": "SCROLL_MOUSE", "clicks": clicks, "direction": direction})
            return True

    def press_key(
        self, key: KeyboardKey | str, modifiers: Sequence[KeyboardModifier | str] | None = None
    ) -> bool:
        with self._lock:
            key_str = key.value if hasattr(key, "value") else str(key)
            mods = [m.value if hasattr(m, "value") else str(m) for m in (modifiers or [])]
            self.recorded_actions.append({"action": "PRESS_KEY", "key": key_str, "modifiers": mods})
            return True

    def type_text(self, text: str, interval: float = 0.0) -> bool:
        with self._lock:
            self.recorded_actions.append({"action": "TYPE_TEXT", "text_len": len(text)})
            return True

    def keyboard_shortcut(self, keys: Sequence[KeyboardKey | str]) -> bool:
        with self._lock:
            key_strs = [k.value if hasattr(k, "value") else str(k) for k in keys]
            self.recorded_actions.append({"action": "KEYBOARD_SHORTCUT", "keys": key_strs})
            return True

    def get_active_window(self) -> WindowInfo | None:
        with self._lock:
            for w in self._windows.values():
                if w.focused:
                    return w
            return list(self._windows.values())[0] if self._windows else None

    def list_windows(self, visible_only: bool = True) -> list[WindowInfo]:
        with self._lock:
            wins = list(self._windows.values())
            if visible_only:
                wins = [w for w in wins if w.visible]
            return wins

    def focus_window(self, window_id: str) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            for wid, w in self._windows.items():
                self._windows[wid] = w.model_copy(update={"focused": (wid == window_id)})
            self.recorded_actions.append({"action": "FOCUS_WINDOW", "window_id": window_id})
            return self._windows[window_id]

    def minimize_window(self, window_id: str) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            self._windows[window_id] = self._windows[window_id].model_copy(
                update={"minimized": True, "focused": False}
            )
            return self._windows[window_id]

    def maximize_window(self, window_id: str) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            self._windows[window_id] = self._windows[window_id].model_copy(
                update={"maximized": True, "minimized": False, "focused": True}
            )
            return self._windows[window_id]

    def restore_window(self, window_id: str) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            self._windows[window_id] = self._windows[window_id].model_copy(
                update={"minimized": False, "maximized": False, "focused": True}
            )
            return self._windows[window_id]

    def move_window(self, window_id: str, x: int, y: int) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            self._windows[window_id] = self._windows[window_id].model_copy(update={"x": x, "y": y})
            return self._windows[window_id]

    def resize_window(self, window_id: str, width: int, height: int) -> WindowInfo | None:
        with self._lock:
            if window_id not in self._windows:
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            self._windows[window_id] = self._windows[window_id].model_copy(
                update={"width": width, "height": height}
            )
            return self._windows[window_id]
