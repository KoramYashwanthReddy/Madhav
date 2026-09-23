"""Integration tests for Module 08 Memory Engine REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from madhav.main import app
from madhav.memory.api.routes import set_memory_service
from madhav.memory.services.memory_service import MemoryService


@pytest.fixture(autouse=True)
def reset_memory_service() -> None:
    """Ensure clean MemoryService instance for every test."""
    set_memory_service(MemoryService())


def test_api_create_get_list_and_search_memory() -> None:
    """Verify POST /memories, GET /memories/{id}, GET /memories, and POST /memories/search."""
    client = TestClient(app)

    # 1. Create memory
    create_resp = client.post(
        "/api/v1/memories",
        json={
            "type": "preference",
            "text": "User prefers dark mode UI interface",
            "importance": "high",
            "tags": ["ui", "theme"],
        },
    )
    assert create_resp.status_code == 201
    mem_data = create_resp.json()
    mem_id = mem_data["memory_id"]
    assert mem_data["text"] == "User prefers dark mode UI interface"
    assert mem_data["importance"] == "high"

    # 2. Get memory by ID
    get_resp = client.get(f"/api/v1/memories/{mem_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["memory_id"] == mem_id
    assert get_resp.json()["last_accessed_at"] is not None

    # 3. List memories
    list_resp = client.get("/api/v1/memories")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1

    # 4. Search memories
    search_resp = client.post("/api/v1/memories/search", json={"query": "dark mode"})
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1


def test_api_memory_lifecycle_operations() -> None:
    """Verify archive, restore, and soft delete API endpoints."""
    client = TestClient(app)

    # Create memory
    create_resp = client.post("/api/v1/memories", json={"text": "Lifecycle test memory"})
    mem_id = create_resp.json()["memory_id"]

    # Archive
    arch_resp = client.post(f"/api/v1/memories/{mem_id}/archive")
    assert arch_resp.status_code == 200
    assert arch_resp.json()["status"] == "archived"

    # Restore
    rest_resp = client.post(f"/api/v1/memories/{mem_id}/restore")
    assert rest_resp.status_code == 200
    assert rest_resp.json()["status"] == "active"

    # Soft Delete
    del_resp = client.delete(f"/api/v1/memories/{mem_id}")
    assert del_resp.status_code == 204

    # Get after delete returns 404
    get_del = client.get(f"/api/v1/memories/{mem_id}")
    assert get_del.status_code == 404
