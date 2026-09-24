"""CLI tool for verifying MAX backup archive integrity."""

import argparse
import sys
from max.data_recovery.service import get_data_recovery_service


def main() -> None:
    parser = argparse.ArgumentParser(description="MAX Backup Verification CLI")
    parser.add_argument("--archive", required=True, help="Path to backup archive file")
    parser.add_argument("--checksum", default=None, help="Expected SHA-256 checksum string")
    args = parser.parse_args()

    svc = get_data_recovery_service()
    report = svc.verify_backup(archive_path=args.archive, expected_checksum=args.checksum)

    print("\n--------------------------------------------------")
    print("Backup Verification Report:")
    print(f"  Backup ID:       {report.backup_id}")
    print(f"  Archive Path:    {report.archive_path}")
    print(f"  Valid Integrity: {report.valid}")
    print(f"  Checksum Match:  {report.checksum_matches}")
    print(f"  Decryption OK:   {report.decryption_successful}")
    print(f"  Schema Valid:    {report.schema_valid}")
    if report.error_message:
        print(f"  Error Detail:    {report.error_message}")
    print("--------------------------------------------------")

    sys.exit(0 if report.valid else 1)


if __name__ == "__main__":
    main()
