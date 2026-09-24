# Backup & Restoration Procedures Guide

## Automated & Manual Backup Execution

### Command Line Backup Trigger
```bash
python scripts/backup.py --type FULL
```

### API Endpoint Trigger
```http
POST /api/v1/data-recovery/backups
Content-Type: application/json

{
  "backup_type": "FULL"
}
```

## Backup Integrity Verification
Prior to performing disaster recovery restoration, every backup archive is verified for checksum integrity, key decryption, and schema structure:

```bash
python scripts/verify_backup.py --archive backups/max_backup_20260924T200000Z.json
```

## Disaster Recovery Atomic Restoration
To restore MAX from a verified backup archive:

```bash
python scripts/restore.py --archive backups/max_backup_20260924T200000Z.json
```
