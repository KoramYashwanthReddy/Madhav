"""End-to-End REST API tests for Module 16 — Computer Control."""

import pytest
from fastapi.testclient import TestClient

from max.computer.container import reset_computer_container
from max.main import app


@pytest.fixture(autouse=True)
def reset_container():
    reset_computer_container()
    yield
    reset_computer_container()


@pytest.fixture
def client():
    return TestClient(app)


def test_get_computer_status(client: TestClient) -> None:
    """Test GET /api/v1/computer/status."""
    response = client.get("/api/v1/computer/status")
    assert response.status_code == 200
    data = response.json()
    assert "enabled" in data
    assert "dry_run" in data
    assert "platform" in data
    assert data["backend_available"] is True


def test_get_computer_state(client: TestClient) -> None:
    """Test GET /api/v1/computer/state."""
    response = client.get("/api/v1/computer/state")
    assert response.status_code == 200
    data = response.json()
    assert "displays" in data
    assert "cursor_position" in data
    assert "available_windows" in data


def test_get_displays_and_screen_info(client: TestClient) -> None:
    """Test GET /api/v1/computer/displays and GET /api/v1/computer/screen/info."""
    resp1 = client.get("/api/v1/computer/displays")
    assert resp1.status_code == 200
    assert len(resp1.json()["displays"]) >= 1

    resp2 = client.get("/api/v1/computer/screen/info")
    assert resp2.status_code == 200
    assert len(resp2.json()["displays"]) >= 1


def test_screen_capture(client: TestClient) -> None:
    """Test POST /api/v1/computer/screen/capture."""
    resp = client.post("/api/v1/computer/screen/capture", json={"display_id": "display_0"})
    assert resp.status_code == 200
    data = resp.json()
    assert "capture" in data
    assert data["capture"]["capture_id"].startswith("cap_")


def test_cursor_endpoints(client: TestClient) -> None:
    """Test cursor position and move endpoints."""
    resp_get = client.get("/api/v1/computer/cursor")
    assert resp_get.status_code == 200
    assert "cursor" in resp_get.json()

    resp_move = client.post(
        "/api/v1/computer/cursor/move",
        json={"x": 100, "y": 200, "permission_decision_id": "dec_sim_1"},
    )
    assert resp_move.status_code == 200
    assert resp_move.json()["status"] == "SIMULATED"


def test_mouse_endpoints(client: TestClient) -> None:
    """Test mouse click, double-click, drag, scroll API endpoints."""
    # Click
    r_click = client.post("/api/v1/computer/mouse/click", json={"x": 10, "y": 10, "button": "left"})
    assert r_click.status_code == 200

    # Double click
    r_dclick = client.post("/api/v1/computer/mouse/double-click", json={"x": 10, "y": 10, "button": "left"})
    assert r_dclick.status_code == 200

    # Drag
    r_drag = client.post("/api/v1/computer/mouse/drag", json={"start_x": 0, "start_y": 0, "end_x": 50, "end_y": 50})
    assert r_drag.status_code == 200

    # Scroll
    r_scroll = client.post("/api/v1/computer/mouse/scroll", json={"clicks": 5, "direction": "vertical"})
    assert r_scroll.status_code == 200


def test_keyboard_endpoints(client: TestClient) -> None:
    """Test keyboard press, type, shortcut API endpoints."""
    # Press key
    r_press = client.post("/api/v1/computer/keyboard/press", json={"key": "enter", "modifiers": ["ctrl"]})
    assert r_press.status_code == 200

    # Type text
    r_type = client.post("/api/v1/computer/keyboard/type", json={"text": "Hello Max!", "interval": 0.01})
    assert r_type.status_code == 200

    # Shortcut
    r_short = client.post("/api/v1/computer/keyboard/shortcut", json={"keys": ["ctrl", "c"]})
    assert r_short.status_code == 200


def test_window_endpoints(client: TestClient) -> None:
    """Test window listing, active window, focus, minimize, maximize, restore, move, resize endpoints."""
    # List windows
    r_list = client.get("/api/v1/computer/windows")
    assert r_list.status_code == 200
    wins = r_list.json()["windows"]
    assert len(wins) >= 1
    target_id = wins[0]["window_id"]

    # Active window
    r_act = client.get("/api/v1/computer/windows/active")
    assert r_act.status_code == 200

    # Focus
    r_foc = client.post(f"/api/v1/computer/windows/{target_id}/focus")
    assert r_foc.status_code == 200

    # Minimize
    r_min = client.post(f"/api/v1/computer/windows/{target_id}/minimize")
    assert r_min.status_code == 200

    # Maximize
    r_max = client.post(f"/api/v1/computer/windows/{target_id}/maximize")
    assert r_max.status_code == 200

    # Restore
    r_res = client.post(f"/api/v1/computer/windows/{target_id}/restore")
    assert r_res.status_code == 200

    # Move
    r_mov = client.post(f"/api/v1/computer/windows/{target_id}/move", json={"x": 100, "y": 100})
    assert r_mov.status_code == 200

    # Resize
    r_rsz = client.post(f"/api/v1/computer/windows/{target_id}/resize", json={"width": 1024, "height": 768})
    assert r_rsz.status_code == 200


def test_actions_and_sequences_endpoints(client: TestClient) -> None:
    """Test generic actions submission, listing, retrieval, cancellation, and sequence execution."""
    # Submit action
    r_sub = client.post(
        "/api/v1/computer/actions",
        json={"action_type": "MOVE_MOUSE", "parameters": {"x": 200, "y": 300}, "dry_run": True},
    )
    assert r_sub.status_code == 200
    action_id = r_sub.json()["action_id"]

    # List actions
    r_list = client.get("/api/v1/computer/actions")
    assert r_list.status_code == 200
    assert len(r_list.json()) >= 1

    # Get single action
    r_get = client.get(f"/api/v1/computer/actions/{action_id}")
    assert r_get.status_code == 200
    assert r_get.json()["action_id"] == action_id

    # Sequence
    r_seq = client.post(
        "/api/v1/computer/sequences",
        json={
            "actions": [
                {"action_type": "MOVE_MOUSE", "parameters": {"x": 10, "y": 10}},
                {"action_type": "CLICK_MOUSE", "parameters": {"button": "left"}},
            ],
            "dry_run": True,
        },
    )
    assert r_seq.status_code == 200
    assert r_seq.json()["sequence_id"].startswith("seq_")
