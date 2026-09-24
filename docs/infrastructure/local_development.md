# Local Development Setup Guide (Target 1)

## Architecture Overview
The local development environment uses Docker Compose to orchestrate dependencies (PostgreSQL, Redis, MinIO) alongside the MAX Python backend API server, background worker, and frontend static dev builds on Windows + WSL2 + Docker Desktop.

## Prerequisites
- Windows 11 with WSL2 (Ubuntu)
- Docker Desktop with WSL2 backend integration enabled
- Python 3.12+ with `uv` or `pip`
- Node.js 20+

## Quick Start Command

1. Copy development environment configuration:
   ```bash
   cp .env.example .env
   ```

2. Start infrastructure dependencies (PostgreSQL, Redis, MinIO, Backend):
   ```bash
   docker compose -f infra/compose/docker-compose.dev.yml up -d
   ```

3. Verify service health and readiness:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   curl http://localhost:8000/api/v1/infrastructure/status
   ```

4. Run the Python backend locally in hot-reload dev mode:
   ```bash
   python scripts/dev.py
   ```

5. Access local endpoints:
   - **MAX API Endpoint**: `http://localhost:8000`
   - **Interactive OpenAPI Docs**: `http://localhost:8000/api/v1/docs`
   - **MinIO Console**: `http://localhost:9001` (User: `minioadmin` / Pass: `minioadmin`)
