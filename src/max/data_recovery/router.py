"""FastAPI Router for Module 39 — Data, Storage, Backup & Disaster Recovery endpoints."""

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel, Field

from max.core.request_id import get_request_id
from max.core.responses import APIResponse
from max.data_recovery.backup import BackupMetadata
from max.data_recovery.classification import DataClassificationTag
from max.data_recovery.migration import MigrationStatus
from max.data_recovery.restore import RestoreReport
from max.data_recovery.retention import RetentionPruneResult
from max.data_recovery.service import DataRecoveryService, get_data_recovery_service
from max.data_recovery.verification import VerificationReport

router = APIRouter(prefix="/data-recovery", tags=["Data, Storage & Disaster Recovery"])


class CreateBackupRequest(BaseModel):
    """Request payload for triggering system backup archive creation."""

    backup_type: str = Field(default="FULL", description="Backup type (FULL, INCREMENTAL, CONFIG_ONLY)")


class VerifyBackupRequest(BaseModel):
    """Request payload for verifying backup archive integrity."""

    archive_path: str = Field(..., description="Filepath to backup archive file")
    checksum_sha256: str | None = Field(default=None, description="Expected SHA-256 checksum for verification")


class RestoreBackupRequest(BaseModel):
    """Request payload for executing disaster recovery restoration."""

    archive_path: str = Field(..., description="Filepath to verified backup archive file")


class EncryptPayloadRequest(BaseModel):
    """Request payload for encryption/decryption utility."""

    text: str = Field(..., description="Text payload to encrypt or decrypt")


@router.post("/backups", response_model=APIResponse[BackupMetadata])
async def create_backup(
    req: CreateBackupRequest = Body(default_factory=CreateBackupRequest),
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[BackupMetadata]:
    """Execute atomic system backup across PostgreSQL, Redis, MinIO, and configuration."""
    metadata = svc.create_backup(backup_type=req.backup_type)
    return APIResponse(
        success=True,
        data=metadata,
        request_id=get_request_id(),
    )


@router.get("/backups", response_model=APIResponse[list[BackupMetadata]])
async def list_backups(
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[list[BackupMetadata]]:
    """List available backup archives and inventory metadata."""
    backups = svc.list_backups()
    return APIResponse(
        success=True,
        data=backups,
        request_id=get_request_id(),
    )


@router.post("/backups/verify", response_model=APIResponse[VerificationReport])
async def verify_backup(
    req: VerifyBackupRequest,
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[VerificationReport]:
    """Verify checksum, decryption, and schema integrity of a backup archive."""
    report = svc.verify_backup(archive_path=req.archive_path, expected_checksum=req.checksum_sha256)
    return APIResponse(
        success=True,
        data=report,
        request_id=get_request_id(),
    )


@router.post("/restore", response_model=APIResponse[RestoreReport])
async def restore_backup(
    req: RestoreBackupRequest,
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[RestoreReport]:
    """Execute disaster recovery atomic restoration from verified backup archive."""
    report = svc.restore_backup(archive_path=req.archive_path)
    return APIResponse(
        success=report.success,
        data=report,
        request_id=get_request_id(),
    )


@router.get("/classification", response_model=APIResponse[DataClassificationTag])
async def classify_domain(
    domain: str = Query(..., description="Subsystem domain identifier (identity, memory, knowledge, logs)"),
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[DataClassificationTag]:
    """Retrieve data sensitivity classification and retention policy tag for a domain."""
    tag = svc.classify_domain(domain_name=domain)
    return APIResponse(
        success=True,
        data=tag,
        request_id=get_request_id(),
    )


@router.post("/encrypt", response_model=APIResponse[dict[str, str]])
async def encrypt_payload(
    req: EncryptPayloadRequest,
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[dict[str, str]]:
    """Encrypt sensitive text payload at-rest using AES-256 / Fernet."""
    cipher = svc.encrypt_payload(req.text)
    return APIResponse(
        success=True,
        data={"ciphertext": cipher},
        request_id=get_request_id(),
    )


@router.post("/decrypt", response_model=APIResponse[dict[str, str]])
async def decrypt_payload(
    req: EncryptPayloadRequest,
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[dict[str, str]]:
    """Decrypt ciphertext payload back to plaintext."""
    plaintext = svc.decrypt_payload(req.text)
    return APIResponse(
        success=True,
        data={"plaintext": plaintext},
        request_id=get_request_id(),
    )


@router.post("/retention/prune", response_model=APIResponse[RetentionPruneResult])
async def prune_expired_data(
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[RetentionPruneResult]:
    """Trigger automated retention pruning run to hard-purge expired tombstones."""
    res = svc.prune_expired_data()
    return APIResponse(
        success=True,
        data=res,
        request_id=get_request_id(),
    )


@router.get("/migrations/status", response_model=APIResponse[MigrationStatus])
async def get_migration_status(
    svc: DataRecoveryService = Depends(get_data_recovery_service),
) -> APIResponse[MigrationStatus]:
    """Retrieve database schema migration status and history."""
    status = svc.get_migration_status()
    return APIResponse(
        success=True,
        data=status,
        request_id=get_request_id(),
    )
