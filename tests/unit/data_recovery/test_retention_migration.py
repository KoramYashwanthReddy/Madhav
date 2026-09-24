"""Unit tests for Data Retention, Tombstone Soft-Delete, and Migration Manager."""

from max.data_recovery.classification import ClassificationLevel
from max.data_recovery.migration import MigrationManager
from max.data_recovery.retention import RetentionManager


def test_retention_policy_resolution() -> None:
    rm = RetentionManager()
    policy_critical = rm.get_policy(ClassificationLevel.CRITICAL)
    assert policy_critical.retention_days == 365
    assert policy_critical.soft_delete_ttl_days == 60

    policy_internal = rm.get_policy(ClassificationLevel.INTERNAL)
    assert policy_internal.retention_days >= 30


def test_soft_delete_tombstone() -> None:
    rm = RetentionManager()
    tombstone = rm.mark_soft_delete(entity_id="conv_123", domain_name="conversation")

    assert tombstone["entity_id"] == "conv_123"
    assert tombstone["domain"] == "conversation"
    assert tombstone["is_deleted"] is True
    assert "purge_due_at" in tombstone


def test_prune_run_execution() -> None:
    rm = RetentionManager()
    result = rm.execute_prune_run()

    assert result.records_scanned >= 0
    assert result.bytes_freed >= 0


def test_migration_status() -> None:
    mm = MigrationManager()
    status = mm.get_status()

    assert status.is_up_to_date is True
    assert len(status.applied_migrations) > 0
    assert status.current_version == "v39_data_recovery_schema"
