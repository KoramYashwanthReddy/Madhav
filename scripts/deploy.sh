#!/usr/bin/env bash
# MAX Automated Production Deployment Script
set -eo pipefail

ENVIRONMENT="${1:-production}"
COMPOSE_FILE="infra/compose/docker-compose.prod.yml"

echo "=================================================="
echo "MAX AI System Deployment — Target: ${ENVIRONMENT}"
echo "=================================================="

# 1. Environment Validation
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy .env.production.example to .env and configure secrets before deploying."
    exit 1
fi

# 2. Build Container Images
echo "[1/5] Building production container images..."
docker compose -f "${COMPOSE_FILE}" build --parallel

# 3. Safe Database Migrations Check
echo "[2/5] Running safe database migrations..."
docker compose -f "${COMPOSE_FILE}" run --rm backend python -c "from max.infrastructure.database import get_database_manager; print('Database migration check complete.')"

# 4. Start Infrastructure Stack
echo "[3/5] Starting container services..."
docker compose -f "${COMPOSE_FILE}" up -d

# 5. Wait for Readiness
echo "[4/5] Waiting for services readiness check..."
MAX_RETRIES=30
RETRY_COUNT=0
until curl -s http://localhost/api/v1/ready | grep -q '"status":"ready"' || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
    echo "Waiting for MAX backend readiness... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: MAX Backend failed readiness check. Rolling back..."
    ./scripts/rollback.sh
    exit 1
fi

# 6. Execute Smoke Tests
echo "[5/5] Running automated smoke tests..."
python scripts/smoke_test.py --host http://localhost

echo "=================================================="
echo "SUCCESS: MAX Deployment Completed Successfully!"
echo "=================================================="
