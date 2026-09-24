"""Integration tests for Module 39 — Data, Storage, Backup & Disaster Recovery API routes."""

import pytest
from fastapi.testclient import TestClient

from max.core.application import create_app


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_create_and_list_backups_api(client: TestClient) -> None:
    # 1. Create Backup via API
    resp_create = client.post("/api/v1/data-recovery/backups", json={"backup_type": "FULL"})
    assert resp_create.status_code == 200
    create_data = resp_create.json()
    assert create_data["success"] is True
    archive_path = create_data["data"]["archive_path"]
    checksum = create_data["data"]["checksum_sha256"]

    # 2. List Backups via API
    resp_list = client.get("/api/v1/data-recovery/backups")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert list_data["success"] is True
    assert len(list_data["data"]) > 0

    # 3. Verify Backup via API
    resp_verify = client.post(
        "/api/v1/data-recovery/backups/verify",
        json={"archive_path": archive_path, "checksum_sha256": checksum},
    )
    assert resp_verify.status_code == 200
    verify_data = resp_verify.json()
    assert verify_data["success"] is True
    assert verify_data["data"]["valid"] is True

    # 4. Disaster Recovery Restore via API
    resp_restore = client.post(
        "/api/v1/data-recovery/restore",
        json={"archive_path": archive_path},
    )
    assert resp_restore.status_code == 200
    restore_data = resp_restore.json()
    assert restore_data["success"] is True
    assert restore_data["data"]["success"] is True


def test_classification_api(client: TestClient) -> None:
    response = client.get("/api/v1/data-recovery/classification?domain=identity")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["level"] == "CRITICAL"


def test_encryption_decryption_api(client: TestClient) -> None:
    # 1. Encrypt
    plaintext = "Top Secret Personal Notes 456"
    resp_enc = client.post("/api/v1/data-recovery/encrypt", json={"text": plaintext})
    assert resp_enc.status_code == 200
    ciphertext = resp_enc.json()["data"]["ciphertext"]

    # 2. Decrypt
    resp_dec = client.post("/api/v1/data-recovery/decrypt", json={"text": ciphertext})
    assert resp_dec.status_code == 200
    decrypted = resp_dec.json()["data"]["plaintext"]
    assert decrypted == plaintext


def test_retention_prune_api(client: TestClient) -> None:
    response = client.post("/api/v1/data-recovery/retention/prune")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "records_scanned" in data["data"]


def test_migrations_status_api(client: TestClient) -> None:
    response = client.get("/api/v1/data-recovery/migrations/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_up_to_date"] is True
