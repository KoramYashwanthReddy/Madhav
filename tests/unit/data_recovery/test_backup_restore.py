"""Unit tests for Backup, Verification, and Disaster Recovery Restoration Engine."""

import os
import pytest
from max.data_recovery.backup import BackupManager
from max.data_recovery.restore import DisasterRecoveryManager
from max.data_recovery.verification import BackupVerifier


def test_backup_creation_and_listing(tmp_path: pytest.TempPathFactory) -> None:
    bm = BackupManager()
    meta = bm.create_backup(backup_type="FULL")

    assert meta.backup_id.startswith("max_backup_")
    assert os.path.exists(meta.archive_path)
    assert meta.size_bytes > 0
    assert len(meta.checksum_sha256) == 64

    backups = bm.list_backups()
    assert len(backups) > 0


def test_backup_verification() -> None:
    bm = BackupManager()
    meta = bm.create_backup(backup_type="FULL")

    verifier = BackupVerifier()
    report = verifier.verify_backup(meta.archive_path, expected_checksum=meta.checksum_sha256)

    assert report.valid is True
    assert report.checksum_matches is True
    assert report.decryption_successful is True
    assert report.schema_valid is True


def test_disaster_recovery_restoration() -> None:
    bm = BackupManager()
    meta = bm.create_backup(backup_type="FULL")

    drm = DisasterRecoveryManager()
    report = drm.restore_from_backup(meta.archive_path)

    assert report.success is True
    assert "postgresql" in report.components_restored
    assert "redis" in report.components_restored
    assert "minio" in report.components_restored
    assert report.execution_time_seconds >= 0.0
