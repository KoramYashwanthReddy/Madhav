# Module 39 — Data, Storage, Backup & Disaster Recovery

## Overview
Module 39 provides production data management, data classification, at-rest encryption, automated backups, checksum verification, atomic disaster recovery restoration, retention policies with soft-delete tombstones, and versioned schema migration management for the MAX Personal AI Operating System.

## Components Implemented
- **Data Classification Engine (`classification.py`)**: Data sensitivity taxonomy (`PUBLIC`, `INTERNAL`, `SENSITIVE`, `CONFIDENTIAL`, `CRITICAL`), domain classification, and payload PII inspection.
- **At-Rest Encryption Manager (`encryption.py`)**: Fernet / AES-256 payload and field encryption with PBKDF2HMAC key derivation.
- **Backup Manager (`backup.py`)**: Automated snapshot generator covering PostgreSQL, Redis, MinIO storage manifests, and platform configurations with SHA-256 checksum computation.
- **Backup Verification Engine (`verification.py`)**: Pre-restoration integrity checks, checksum validation, decryption tests, and schema verification.
- **Disaster Recovery Restore Engine (`restore.py`)**: Atomic multi-component restoration from verified backup archives.
- **Retention & Lifecycle Manager (`retention.py`)**: Retention policies, soft-delete tombstones (`mark_soft_delete`), and automated hard purging (`execute_prune_run`).
- **Schema Migration Manager (`migration.py`)**: Migration version tracking, forward execution, and rollback support.
- **Data Recovery Service (`service.py`)**: Centralized facade integrating all Module 39 functions.
- **API Router (`router.py`)**: REST API endpoints under `/api/v1/data-recovery`.
- **Operational CLI Tools (`scripts/`)**: `scripts/backup.py`, `scripts/verify_backup.py`, `scripts/restore.py`.
