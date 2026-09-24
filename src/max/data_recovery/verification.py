"""Backup Verification Engine and Integrity Inspector."""

import hashlib
import json
import logging
import os
from typing import Any
from pydantic import BaseModel, Field

from max.config.settings import Settings, get_settings
from max.data_recovery.encryption import DataEncryptionManager

logger = logging.getLogger(__name__)


class VerificationReport(BaseModel):
    """Detailed verification report for a backup archive."""

    backup_id: str = Field(..., description="Backup identifier being verified")
    archive_path: str = Field(..., description="Filepath to backup archive")
    valid: bool = Field(default=True, description="Whether backup passes integrity and decryption checks")
    checksum_matches: bool = Field(default=True, description="Whether calculated SHA-256 matches expected checksum")
    decryption_successful: bool = Field(default=True, description="Whether backup payload was successfully decrypted")
    schema_valid: bool = Field(default=True, description="Whether internal JSON payload structure is valid")
    error_message: str | None = Field(default=None, description="Detailed error message if verification fails")


class BackupVerifier:
    """Verification engine for validating backup archive integrity prior to disaster recovery restoration."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.encryption_mgr = DataEncryptionManager(self.settings)

    def verify_backup(self, archive_path: str, expected_checksum: str | None = None) -> VerificationReport:
        """Inspect and verify backup archive checksum, decryption, and payload schema."""
        b_id = os.path.basename(archive_path).replace(".json", "")

        if not os.path.exists(archive_path):
            return VerificationReport(
                backup_id=b_id,
                archive_path=archive_path,
                valid=False,
                checksum_matches=False,
                decryption_successful=False,
                schema_valid=False,
                error_message=f"Backup archive file does not exist at path: {archive_path}",
            )

        try:
            with open(archive_path, "rb") as f:
                raw_bytes = f.read()

            # 1. SHA-256 Checksum Verification
            actual_checksum = hashlib.sha256(raw_bytes).hexdigest()
            checksum_matches = True
            if expected_checksum and actual_checksum.lower() != expected_checksum.lower():
                checksum_matches = False

            # 2. Decryption Verification
            try:
                decrypted_bytes = self.encryption_mgr.decrypt_bytes(raw_bytes)
                decryption_ok = True
            except Exception as exc:
                return VerificationReport(
                    backup_id=b_id,
                    archive_path=archive_path,
                    valid=False,
                    checksum_matches=checksum_matches,
                    decryption_successful=False,
                    schema_valid=False,
                    error_message=f"Decryption failed: {exc}",
                )

            # 3. Payload Schema Integrity Verification
            try:
                payload = json.loads(decrypted_bytes.decode("utf-8"))
                has_required_keys = all(k in payload for k in ("backup_id", "timestamp", "database_snapshot", "config_snapshot"))
                schema_ok = has_required_keys
            except Exception as exc:
                return VerificationReport(
                    backup_id=b_id,
                    archive_path=archive_path,
                    valid=False,
                    checksum_matches=checksum_matches,
                    decryption_successful=True,
                    schema_valid=False,
                    error_message=f"Invalid JSON payload schema: {exc}",
                )

            is_valid = checksum_matches and decryption_ok and schema_ok

            return VerificationReport(
                backup_id=b_id,
                archive_path=archive_path,
                valid=is_valid,
                checksum_matches=checksum_matches,
                decryption_successful=decryption_ok,
                schema_valid=schema_ok,
                error_message=None if is_valid else "Backup validation check failed",
            )

        except Exception as exc:
            logger.error("Verification process error for %s: %s", archive_path, exc)
            return VerificationReport(
                backup_id=b_id,
                archive_path=archive_path,
                valid=False,
                checksum_matches=False,
                decryption_successful=False,
                schema_valid=False,
                error_message=str(exc),
            )
