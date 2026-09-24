#!/usr/bin/env bash
# MAX Production Rollback Script
set -eo pipefail

COMPOSE_FILE="infra/compose/docker-compose.prod.yml"

echo "=================================================="
echo "MAX AI System Rollback Sequence Initiated"
echo "=================================================="

# 1. Stop Failing Services
echo "[1/3] Stopping container services..."
docker compose -f "${COMPOSE_FILE}" stop backend worker scheduler reverse-proxy

# 2. Restart Containers with Previous Stable Images
echo "[2/3] Restarting services with previous container builds..."
docker compose -f "${COMPOSE_FILE}" up -d --no-build

# 3. Verify Health Post-Rollback
echo "[3/3] Verifying health status post-rollback..."
sleep 5
if curl -s http://localhost/health | grep -q '"status":"ok"'; then
    echo "Rollback successful. Container health restored."
else
    echo "WARNING: Post-rollback health check failed. System requires manual investigation."
fi

echo "=================================================="
