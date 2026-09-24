"""Unit tests for mock backend and platform detection."""

from max.computer.backends.mock import MockComputerControlBackend
from max.computer.backends.platform_detector import PlatformDetector
from max.computer.domain.enums import MouseButton, PlatformType


def test_platform_detector() -> None:
    """Test platform detection returns valid PlatformType."""
    plat = PlatformDetector.detect()
    assert isinstance(plat, PlatformType)


def test_mock_backend_primitives() -> None:
    """Test deterministic mock backend computer control primitives."""
    backend = MockComputerControlBackend()
    assert backend.is_available() is True

    # Displays
    displays = backend.get_displays()
    assert len(displays) >= 1
    assert displays[0].display_id == "display_0"

    # Cursor position & mouse move
    pos = backend.get_cursor_position()
    assert pos.x == 100 and pos.y == 100
    moved_pos = backend.move_mouse(100, 200)
    assert moved_pos.x == 100 and moved_pos.y == 200

    # Click & Drag
    click_pos = backend.click_mouse(150, 250, button=MouseButton.LEFT)
    assert click_pos.x == 150 and click_pos.y == 250
    drag_pos = backend.drag_mouse(0, 0, 300, 400)
    assert drag_pos.x == 300 and drag_pos.y == 400

    # Screen capture
    cap = backend.capture_screen(display_id="display_0")
    assert cap.width == displays[0].width
    assert cap.image_reference is not None

    # Windows
    windows = backend.list_windows()
    assert len(windows) >= 1
    active_win = backend.get_active_window()
    assert active_win is not None
    focused = backend.focus_window(windows[0].window_id)
    assert focused is not None and focused.focused is True
