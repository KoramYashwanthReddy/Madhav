# SRE & Production Incident Runbooks

## Runbook 1: MAX Backend Service Degradation or Outage

### Symptoms
- Liveness `/health` or readiness `/ready` returns HTTP 500/503.
- Reverse proxy returns 502 Bad Gateway.

### Diagnostic & Resolution Steps
1. Check container running status:
   ```bash
   docker compose -f infra/compose/docker-compose.prod.yml ps
   ```
2. View backend logs:
   ```bash
   docker compose -f infra/compose/docker-compose.prod.yml logs -f --tail=100 backend
   ```
3. Restart backend service gracefully:
   ```bash
   docker compose -f infra/compose/docker-compose.prod.yml restart backend
   ```

---

## Runbook 2: PostgreSQL Database Connectivity Failure

### Symptoms
- Readiness `/ready` reports `postgresql_database: unready`.
- API endpoints depending on persistence fail.

### Diagnostic & Resolution Steps
1. Verify PostgreSQL container status:
   ```bash
   docker compose -f infra/compose/docker-compose.prod.yml exec postgres pg_isready -U max -d maxdb
   ```
2. Check disk space on host:
   ```bash
   df -h
   ```
3. Check PostgreSQL connection limits and pool status:
   ```bash
   curl http://localhost:8000/api/v1/infrastructure/status
   ```

---

## Runbook 3: Emergency Automated Rollback

### Trigger Condition
Failed deployment or severe regression post-release.

### Action
Execute rollback script:
```bash
./scripts/rollback.sh
```
Verify post-rollback health:
```bash
python scripts/smoke_test.py --host http://localhost:8000
```
