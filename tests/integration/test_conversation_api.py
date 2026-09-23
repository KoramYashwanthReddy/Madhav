"""Integration tests for Module 07 Conversation Engine REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from madhav.conversation.api.routes import set_conversation_service
from madhav.conversation.services.conversation_service import ConversationService
from madhav.main import app


@pytest.fixture(autouse=True)
def reset_conversation_service() -> None:
    """Ensure clean ConversationService instance for every test."""
    set_conversation_service(ConversationService())


def test_api_create_list_and_get_conversation() -> None:
    """Verify POST /conversations, GET /conversations, and GET /conversations/{id}."""
    client = TestClient(app)

    # 1. Create conversation
    create_resp = client.post(
        "/api/v1/conversations",
        json={"title": "Integration Test Conv", "model_reference": "development-stub"},
    )
    assert create_resp.status_code == 201
    conv_data = create_resp.json()
    conv_id = conv_data["conversation_id"]
    assert conv_data["title"] == "Integration Test Conv"
    assert conv_data["status"] == "active"

    # 2. Get conversation by ID
    get_resp = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["conversation_id"] == conv_id

    # 3. List conversations
    list_resp = client.get("/api/v1/conversations")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert list_data["total"] >= 1
    assert any(c["conversation_id"] == conv_id for c in list_data["conversations"])


def test_api_conversation_turn_execution() -> None:
    """Verify POST /conversations/{id}/messages executes turn and returns assistant response."""
    client = TestClient(app)

    # Create conversation
    create_resp = client.post("/api/v1/conversations", json={})
    conv_id = create_resp.json()["conversation_id"]

    # Send message / execute turn
    turn_resp = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hello Madhav, what is FastAPI?"},
    )
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()

    assert turn_data["user_message"]["content"] == "Hello Madhav, what is FastAPI?"
    assert turn_data["user_message"]["role"] == "user"
    assert turn_data["assistant_message"]["role"] == "assistant"
    assert len(turn_data["assistant_message"]["content"]) > 0

    # Verify title auto-generated
    assert turn_data["conversation"]["title"] == "Hello Madhav, what is FastAPI?"

    # List messages
    msgs_resp = client.get(f"/api/v1/conversations/{conv_id}/messages")
    assert msgs_resp.status_code == 200
    msgs_data = msgs_resp.json()
    assert msgs_data["total_messages"] == 2


def test_api_archive_restore_and_delete() -> None:
    """Verify archiving, restoring, and deleting a conversation via REST API."""
    client = TestClient(app)

    # Create conversation
    create_resp = client.post("/api/v1/conversations", json={"title": "Lifecycle Conv"})
    conv_id = create_resp.json()["conversation_id"]

    # Archive
    arch_resp = client.post(f"/api/v1/conversations/{conv_id}/archive")
    assert arch_resp.status_code == 200
    assert arch_resp.json()["status"] == "archived"

    # Send message on archived conv should return 409 Conflict
    err_resp = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Message to archived conversation"},
    )
    assert err_resp.status_code == 409

    # Restore
    rest_resp = client.post(f"/api/v1/conversations/{conv_id}/restore")
    assert rest_resp.status_code == 200
    assert rest_resp.json()["status"] == "active"

    # Send message now works
    msg_resp = client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Message after restore"},
    )
    assert msg_resp.status_code == 200

    # Soft Delete
    del_resp = client.delete(f"/api/v1/conversations/{conv_id}")
    assert del_resp.status_code == 204

    # Getting deleted conv returns 404
    get_del = client.get(f"/api/v1/conversations/{conv_id}")
    assert get_del.status_code == 404
