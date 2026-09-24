"""CLI tool for executing MAX disaster recovery restoration."""

import argparse
import sys
from max.data_recovery.service import get_data_recovery_service


def main() -> None:
    parser = argparse.ArgumentParser(description="MAX Disaster Recovery Restoration CLI")
    parser.add_argument("--archive", required=True, help="Path to verified backup archive file")
    args = parser.parse_args()

    print(f"Initiating Disaster Recovery Restoration from: {args.archive}")
    svc = get_data_recovery_service()
    report = svc.restore_backup(archive_path=args.archive)

    print("\n--------------------------------------------------")
    print("Disaster Recovery Restoration Report:")
    print(f"  Backup ID:           {report.backup_id}")
    print(f"  Restoration Success: {report.success}")
    print(f"  Components Restored: {', '.join(report.components_restored)}")
    print(f"  Execution Duration:  {report.execution_time_seconds:.3f} seconds")
    if report.error_detail:
        print(f"  Error Detail:        {report.error_detail}")
    print("--------------------------------------------------")

    sys.exit(0 if report.success else 1)


if __name__ == "__main__":
    main()
