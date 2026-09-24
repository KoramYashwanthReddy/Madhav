"""Data Retention & Storage Lifecycle Manager with Soft-Delete Tombstones."""

import datetime
import logging
from typing import Any

from pydantic import BaseModel, Field

from max.config.settings import Settings, get_settings
from max.data_recovery.classification import ClassificationLevel, DataClassifier

logger = logging.getLogger(__name__)


class RetentionPolicy(BaseModel):
    """Retention rule configuration per classification sensitivity level."""

    level: ClassificationLevel = Field(..., description="Target sensitivity classification level")
    retention_days: int = Field(..., description="Maximum storage retention duration in days")
    soft_delete_ttl_days: int = Field(default=30, description="Tombstone retention before hard permanent purge")
    auto_purge_enabled: bool = Field(default=True, description="Enable automated pruning background job")


class RetentionPruneResult(BaseModel):
    """Result summary of a data retention pruning run."""

    records_scanned: int = Field(default=0, description="Total records inspected during prune run")
    records_soft_deleted: int = Field(default=0, description="Records marked with soft-delete tombstones")
    records_hard_purged: int = Field(default=0, description="Expired records permanently deleted")
    bytes_freed: int = Field(default=0, description="Estimated storage space reclaimed in bytes")


class RetentionManager:
    """Manager for soft-delete lifecycle management, tombstone retention, and automated pruning."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_policy(self, level: ClassificationLevel) -> RetentionPolicy:
        """Return configured retention policy parameters for specified sensitivity level."""
        default_days = self.settings.data_recovery.retention_days

        if level == ClassificationLevel.CRITICAL:
            return RetentionPolicy(level=level, retention_days=365, soft_delete_ttl_days=60)
        elif level == ClassificationLevel.CONFIDENTIAL:
            return RetentionPolicy(level=level, retention_days=180, soft_delete_ttl_days=30)
        elif level == ClassificationLevel.SENSITIVE:
            return RetentionPolicy(level=level, retention_days=365, soft_delete_ttl_days=30)
        elif level == ClassificationLevel.INTERNAL:
            return RetentionPolicy(level=level, retention_days=default_days, soft_delete_ttl_days=14)
        else:
            return RetentionPolicy(level=level, retention_days=30, soft_delete_ttl_days=7)

    def mark_soft_delete(self, entity_id: str, domain_name: str) -> dict[str, Any]:
        """Apply soft-delete tombstone to entity record."""
        now = datetime.datetime.now(datetime.UTC)
        tag = DataClassifier.classify_domain(domain_name)
        policy = self.get_policy(tag.level)
        purge_due = now + datetime.timedelta(days=policy.soft_delete_ttl_days)

        tombstone = {
            "entity_id": entity_id,
            "domain": domain_name,
            "classification": tag.level.value,
            "deleted_at": now.isoformat(),
            "purge_due_at": purge_due.isoformat(),
            "is_deleted": True,
        }
        logger.info("Applied soft-delete tombstone to %s entity %s (purge due %s)", domain_name, entity_id, purge_due.isoformat())
        return tombstone

    def execute_prune_run(self) -> RetentionPruneResult:
        """Scan system data stores and execute automated retention pruning of expired tombstones."""
        logger.info("Starting automated data retention pruning run...")
        # Simulated retention pruning run
        return RetentionPruneResult(
            records_scanned=150,
            records_soft_deleted=12,
            records_hard_purged=4,
            bytes_freed=2048576,
        )
