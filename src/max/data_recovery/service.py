"""Centralized Data Recovery Service Facade for Module 39."""

import logging
from typing import Any

from max.config.settings import Settings, get_settings
from max.data_recovery.backup import BackupManager, BackupMetadata
from max.data_recovery.classification import ClassificationLevel, DataClassificationTag, DataClassifier
from max.data_recovery.encryption import DataEncryptionManager
from max.data_recovery.migration import MigrationManager, MigrationStatus
from max.data_recovery.restore import DisasterRecoveryManager, RestoreReport
from max.data_recovery.retention import RetentionManager, RetentionPolicy, RetentionPruneResult
from max.data_recovery.verification import BackupVerifier, VerificationReport

logger = logging.getLogger(__name__)


class DataRecoveryService:
    """Centralized facade coordinating classification, encryption, backups, verification, DR restoration, retention, and migrations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.classifier = DataClassifier()
        self.encryption = DataEncryptionManager(self.settings)
        self.backup_mgr = BackupManager(self.settings)
        self.verifier = BackupVerifier(self.settings)
        self.restore_mgr = DisasterRecoveryManager(self.settings)
        self.retention_mgr = RetentionManager(self.settings)
        self.migration_mgr = MigrationManager(self.settings)

    def classify_domain(self, domain_name: str) -> DataClassificationTag:
        """Classify subsystem domain sensitivity and retention policy."""
        return self.classifier.classify_domain(domain_name)

    def encrypt_payload(self, text: str) -> str:
        """Encrypt plaintext payload using Fernet / AES-256."""
        return self.encryption.encrypt_string(text)

    def decrypt_payload(self, ciphertext: str) -> str:
        """Decrypt ciphertext payload back to plaintext."""
        return self.encryption.decrypt_string(ciphertext)

    def create_backup(self, backup_type: str = "FULL") -> BackupMetadata:
        """Execute atomic system backup across PostgreSQL, Redis, MinIO, and config."""
        return self.backup_mgr.create_backup(backup_type)

    def list_backups(self) -> list[BackupMetadata]:
        """List existing backup archives."""
        return self.backup_mgr.list_backups()

    def verify_backup(self, archive_path: str, expected_checksum: str | None = None) -> VerificationReport:
        """Verify checksum, decryption, and schema integrity of backup archive."""
        return self.verifier.verify_backup(archive_path, expected_checksum)

    def restore_backup(self, archive_path: str) -> RestoreReport:
        """Execute disaster recovery atomic restoration from verified backup archive."""
        return self.restore_mgr.restore_from_backup(archive_path)

    def prune_expired_data(self) -> RetentionPruneResult:
        """Execute automated retention pruning of expired tombstoned records."""
        return self.retention_mgr.execute_prune_run()

    def get_migration_status(self) -> MigrationStatus:
        """Retrieve schema migration status and applied history."""
        return self.migration_mgr.get_status()


_data_recovery_service_instance: DataRecoveryService | None = None


def get_data_recovery_service() -> DataRecoveryService:
    """Retrieve global singleton DataRecoveryService instance."""
    global _data_recovery_service_instance
    if _data_recovery_service_instance is None:
        _data_recovery_service_instance = DataRecoveryService()
    return _data_recovery_service_instance
