"""Windows 11 ComputerControlBackend implementation using Win32 ctypes."""

import ctypes
import sys
import threading
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from max.computer.backends.base import ComputerControlBackend
from max.computer.domain.enums import KeyboardKey, KeyboardModifier, MouseButton, PlatformType
from max.computer.domain.exceptions import BackendUnavailableError, WindowNotFoundError
from max.computer.domain.models import (
    CursorPosition,
    DisplayInfo,
    ScreenCapture,
    ScreenRegion,
    WindowInfo,
)


class POINT(ctypes.Structure):
    """Win32 POINT structure."""

    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    """Win32 RECT structure."""

    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class WindowsComputerControlBackend(ComputerControlBackend):
    """Windows-native computer control backend using user32.dll / ctypes."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._is_win = sys.platform.startswith("win")
        self._user32: Any = None
        if self._is_win:
            try:
                self._user32 = ctypes.windll.user32
            except Exception:
                self._user32 = None

    @property
    def platform(self) -> PlatformType:
        return PlatformType.WINDOWS

    def is_available(self) -> bool:
        return self._is_win and self._user32 is not None

    def _get_user32(self) -> Any:
        if not self.is_available() or self._user32 is None:
            raise BackendUnavailableError("Windows computer control backend is not available in current environment.")
        return self._user32

    def get_displays(self) -> list[DisplayInfo]:
        user32 = self._get_user32()
        with self._lock:
            width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
            height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
            return [
                DisplayInfo(
                    display_id="display_0",
                    width=width if width > 0 else 1920,
                    height=height if height > 0 else 1080,
                    x=0,
                    y=0,
                    scale_factor=1.0,
                    primary=True,
                )
            ]

    def capture_screen(
        self, display_id: str = "display_0", region: ScreenRegion | None = None
    ) -> ScreenCapture:
        self._get_user32()
        with self._lock:
            displays = self.get_displays()
            disp = displays[0]
            w = region.width if region else disp.width
            h = region.height if region else disp.height

            return ScreenCapture(
                display_id=disp.display_id,
                region=region,
                width=w,
                height=h,
                image_reference="win32_screen_buffer_reference",
                timestamp=datetime.now(UTC),
            )

    def get_cursor_position(self) -> CursorPosition:
        user32 = self._get_user32()
        with self._lock:
            pt = POINT()
            if user32.GetCursorPos(ctypes.byref(pt)):
                return CursorPosition(x=pt.x, y=pt.y, timestamp=datetime.now(UTC))
            return CursorPosition(x=0, y=0, timestamp=datetime.now(UTC))

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> CursorPosition:
        user32 = self._get_user32()
        with self._lock:
            user32.SetCursorPos(int(x), int(y))
            return self.get_cursor_position()

    def click_mouse(
        self,
        x: int | None = None,
        y: int | None = None,
        button: MouseButton = MouseButton.LEFT,
        click_count: int = 1,
    ) -> CursorPosition:
        user32 = self._get_user32()
        with self._lock:
            if x is not None and y is not None:
                self.move_mouse(x, y)

            down_flag, up_flag = 0x0002, 0x0004
            if button == MouseButton.RIGHT:
                down_flag, up_flag = 0x0008, 0x0010
            elif button == MouseButton.MIDDLE:
                down_flag, up_flag = 0x0020, 0x0040

            for _ in range(max(1, click_count)):
                user32.mouse_event(down_flag, 0, 0, 0, 0)
                user32.mouse_event(up_flag, 0, 0, 0, 0)

            return self.get_cursor_position()

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
        user32 = self._get_user32()
        with self._lock:
            self.move_mouse(start_x, start_y)
            down_flag = 0x0002 if button == MouseButton.LEFT else 0x0008
            up_flag = 0x0004 if button == MouseButton.LEFT else 0x0010

            user32.mouse_event(down_flag, 0, 0, 0, 0)
            self.move_mouse(end_x, end_y)
            user32.mouse_event(up_flag, 0, 0, 0, 0)
            return self.get_cursor_position()

    def scroll_mouse(
        self,
        clicks: int,
        direction: str = "vertical",
        x: int | None = None,
        y: int | None = None,
    ) -> bool:
        user32 = self._get_user32()
        with self._lock:
            if x is not None and y is not None:
                self.move_mouse(x, y)
            user32.mouse_event(0x0800, 0, 0, clicks * 120, 0)
            return True

    def press_key(
        self, key: KeyboardKey | str, modifiers: Sequence[KeyboardModifier | str] | None = None
    ) -> bool:
        user32 = self._get_user32()
        with self._lock:
            mod_vks = [self._resolve_vk_code(m) for m in (modifiers or []) if self._resolve_vk_code(m)]
            vk = self._resolve_vk_code(key)

            for m_vk in mod_vks:
                user32.keybd_event(m_vk, 0, 0, 0)

            if vk:
                user32.keybd_event(vk, 0, 0, 0)
                user32.keybd_event(vk, 0, 0x0002, 0)

            for m_vk in reversed(mod_vks):
                user32.keybd_event(m_vk, 0, 0x0002, 0)

            return True

    def type_text(self, text: str, interval: float = 0.0) -> bool:
        user32 = self._get_user32()
        with self._lock:
            for char in text:
                user32.keybd_event(0, ord(char), 0x0004, 0)
                user32.keybd_event(0, ord(char), 0x0004 | 0x0002, 0)
            return True

    def keyboard_shortcut(self, keys: Sequence[KeyboardKey | str]) -> bool:
        if not keys:
            return False
        modifiers = keys[:-1]
        target_key = keys[-1]
        return self.press_key(key=target_key, modifiers=modifiers)

    def get_active_window(self) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
            return self._build_window_info(hwnd, focused=True)

    def list_windows(self, visible_only: bool = True) -> list[WindowInfo]:
        user32 = self._get_user32()
        with self._lock:
            windows: list[WindowInfo] = []
            active_hwnd = user32.GetForegroundWindow()

            def enum_windows_proc(hwnd: int, lparam: int) -> bool:
                if visible_only and not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                if length == 0 and visible_only:
                    return True

                win_info = self._build_window_info(hwnd, focused=(hwnd == active_hwnd))
                if win_info:
                    windows.append(win_info)
                return True

            wnd_enum_proc_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(wnd_enum_proc_type(enum_windows_proc), 0)
            return windows

    def focus_window(self, window_id: str) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
            return self._build_window_info(hwnd, focused=True)

    def minimize_window(self, window_id: str) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
            return self._build_window_info(hwnd)

    def maximize_window(self, window_id: str) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
            return self._build_window_info(hwnd)

    def restore_window(self, window_id: str) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            return self._build_window_info(hwnd)

    def move_window(self, window_id: str, x: int, y: int) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            user32.MoveWindow(hwnd, int(x), int(y), width, height, True)
            return self._build_window_info(hwnd)

    def resize_window(self, window_id: str, width: int, height: int) -> WindowInfo | None:
        user32 = self._get_user32()
        with self._lock:
            hwnd = self._parse_hwnd(window_id)
            if not hwnd or not user32.IsWindow(hwnd):
                raise WindowNotFoundError(f"Window '{window_id}' not found.")
            rect = RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            user32.MoveWindow(hwnd, rect.left, rect.top, int(width), int(height), True)
            return self._build_window_info(hwnd)

    def _parse_hwnd(self, window_id: str) -> int | None:
        try:
            if window_id.startswith("hwnd_"):
                return int(window_id.replace("hwnd_", ""))
            return int(window_id)
        except ValueError:
            return None

    def _build_window_info(self, hwnd: int, focused: bool = False) -> WindowInfo | None:
        user32 = self._get_user32()
        if not user32.IsWindow(hwnd):
            return None
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        title = buf.value

        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

        is_iconic = bool(user32.IsIconic(hwnd))
        is_zoomed = bool(user32.IsZoomed(hwnd))
        is_visible = bool(user32.IsWindowVisible(hwnd))

        return WindowInfo(
            window_id=f"hwnd_{hwnd}",
            title=title,
            process_id=pid.value if pid.value > 0 else None,
            application_identifier=title,
            x=rect.left,
            y=rect.top,
            width=rect.right - rect.left,
            height=rect.bottom - rect.top,
            visible=is_visible,
            minimized=is_iconic,
            maximized=is_zoomed,
            focused=focused,
        )

    def _resolve_vk_code(self, key: KeyboardKey | KeyboardModifier | str) -> int | None:
        k_str = str(key.value if hasattr(key, "value") else key).upper()
        vk_map = {
            "ENTER": 0x0D,
            "ESC": 0x1B,
            "TAB": 0x09,
            "BACKSPACE": 0x08,
            "SPACE": 0x20,
            "DELETE": 0x2E,
            "UP": 0x26,
            "DOWN": 0x28,
            "LEFT": 0x25,
            "RIGHT": 0x27,
            "HOME": 0x24,
            "END": 0x23,
            "PAGE_UP": 0x21,
            "PAGE_DOWN": 0x22,
            "CTRL": 0x11,
            "ALT": 0x12,
            "SHIFT": 0x10,
            "WIN": 0x5B,
            "F1": 0x70,
            "F2": 0x71,
            "F3": 0x72,
            "F4": 0x73,
            "F5": 0x74,
            "F6": 0x75,
            "F7": 0x76,
            "F8": 0x77,
            "F9": 0x78,
            "F10": 0x79,
            "F11": 0x7A,
            "F12": 0x7B,
        }
        if k_str in vk_map:
            return vk_map[k_str]
        if len(k_str) == 1:
            user32 = self._get_user32()
            res = user32.VkKeyScanW(ord(k_str))
            return res & 0xFF if res != -1 else None
        return None
