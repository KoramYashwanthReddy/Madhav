"""End-to-end API tests for Module 17 — Filesystem Agent REST API endpoints."""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from max.filesystem.container import get_filesystem_container, reset_filesystem_container
from max.main import app
from max.security.container import get_security_container, reset_security_container
from max.security.domain import (
    PermissionAction,
    PermissionGrantType,
    PermissionResource,
    PermissionScope,
    PermissionSubject,
    PermissionSubjectType,
)


@pytest.fixture(autouse=True)
def setup_e2e_filesystem():
    """Configure mock container and security grants for E2E tests."""
    reset_filesystem_container()
    reset_security_container()

    container = get_filesystem_container(use_mock_backend=True)

    # Seed explicit permission grants for system test runner
    sec_container = get_security_container()
    subject = PermissionSubject(subject_id="agent_fs", subject_type=PermissionSubjectType.AGENT)
    test_path_resolved = str(Path("C:/tmp/e2e_test_doc.txt").resolve())
    resource = PermissionResource(resource_type="FILE", resource_id=test_path_resolved, owner_id="system")

    for act in [PermissionAction.READ, PermissionAction.WRITE, PermissionAction.MODIFY, PermissionAction.DELETE]:
        sec_container.grant_service.create_grant(
            subject=subject,
            action=act,
            resource=resource,
            owner_id="system",
            grant_type=PermissionGrantType.PERSISTENT,
            scope=PermissionScope.EXACT_RESOURCE,
        )

    yield container
    reset_filesystem_container()
    reset_security_container()


@pytest.fixture
def client():
    """Create FastAPI TestClient."""
    return TestClient(app)


def test_e2e_filesystem_status(client):
    """Test GET /api/v1/filesystem/status."""
    response = client.get("/api/v1/filesystem/status")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert "backend_type" in data
    assert len(data["capabilities"]) > 0


def test_e2e_filesystem_write_read_stat_delete_flow(client):
    """Test full E2E flow: write -> read -> stat -> hash -> delete."""
    test_path = "C:/tmp/e2e_test_doc.txt"

    # 1. Write file
    w_resp = client.post(
        "/api/v1/filesystem/write",
        json={
            "path": test_path,
            "content": "E2E Test File Content",
            "overwrite": True,
        },
    )
    assert w_resp.status_code == 200
    w_data = w_resp.json()
    assert w_data["status"] in ("COMPLETED", "SIMULATED")

    # 2. Read file
    r_resp = client.post(
        "/api/v1/filesystem/read",
        json={"path": test_path},
    )
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["status"] in ("COMPLETED", "SIMULATED")

    # 3. Hash file
    h_resp = client.post(
        "/api/v1/filesystem/hash",
        json={"path": test_path, "algorithm": "sha256"},
    )
    assert h_resp.status_code == 200

    # 4. Delete file
    d_resp = client.post(
        "/api/v1/filesystem/delete",
        json={"path": test_path, "is_directory": False},
    )
    assert d_resp.status_code == 200


def test_e2e_filesystem_operations_audit_list(client):
    """Test GET /api/v1/filesystem/operations."""
    resp = client.get("/api/v1/filesystem/operations")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
