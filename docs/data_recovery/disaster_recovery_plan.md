# Disaster Recovery Plan & Loss Prevention

## Scenarios Covered

1. **Database Corruption**:
   - Issue: Partial or total corruption of PostgreSQL tables.
   - Strategy: Restore latest verified full database dump from backup archive.

2. **Hardware or Host Failure**:
   - Issue: Remote server disk crash or host termination.
   - Strategy: Provision new container environment using `docker-compose.prod.yml`, download latest encrypted remote backup archive, execute `python scripts/restore.py`.

3. **Accidental Deletion**:
   - Issue: Accidental deletion of user memory or conversation history.
   - Strategy: Soft-delete tombstone prevents immediate hard deletion. Tombstones are retained for 30–60 days before automated background purging.

4. **Deployment Failure**:
   - Issue: Failed database migration during version deployment.
   - Strategy: `MigrationManager` verifies migration checksums and permits atomic rollback to target version ID.
