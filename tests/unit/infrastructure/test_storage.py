"""Unit tests for MinIO / S3 Object Storage Infrastructure Manager."""

import pytest

from max.infrastructure.storage import StorageManager, get_storage_manager


@pytest.mark.asyncio
async def test_storage_manager_health() -> None:
    storage_mgr = StorageManager()
    health = await storage_mgr.check_health()

    assert health["status"] == "ok"
    assert health["provider"] == "minio"
    assert health["primary_bucket"] == "max-artifacts"
    assert health["bucket_accessible"] is True


def test_presigned_url_generation() -> None:
    storage_mgr = StorageManager()
    url = storage_mgr.generate_presigned_url(object_name="document.pdf", expires_seconds=1800)

    assert "document.pdf" in url
    assert "max-artifacts" in url
    assert "expires=1800" in url
    assert "sig=" in url


def test_get_storage_manager_singleton() -> None:
    s1 = get_storage_manager()
    s2 = get_storage_manager()
    assert s1 is s2
