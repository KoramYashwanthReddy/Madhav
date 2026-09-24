"""CLI tool for triggering MAX system data backup creation."""

import argparse
import sys
from max.data_recovery.service import get_data_recovery_service


def main() -> None:
    parser = argparse.ArgumentParser(description="MAX Automated Data Backup CLI")
    parser.add_argument("--type", default="FULL", choices=["FULL", "INCREMENTAL", "CONFIG_ONLY"], help="Type of backup")
    args = parser.parse_args()

    print(f"Initiating MAX system backup ({args.type})...")
    svc = get_data_recovery_service()
    meta = svc.create_backup(backup_type=args.type)

    print("\n--------------------------------------------------")
    print("Backup Creation Complete:")
    print(f"  Backup ID:       {meta.backup_id}")
    print(f"  Archive Path:    {meta.archive_path}")
    print(f"  Size:            {meta.size_bytes} bytes")
    print(f"  SHA-256 Checksum: {meta.checksum_sha256}")
    print(f"  Encrypted:       {meta.encrypted}")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
