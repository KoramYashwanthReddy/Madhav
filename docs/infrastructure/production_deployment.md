# Remote Personal Server Production Deployment Guide (Target 2 & 3)

## Architecture
The production deployment runs MAX as a set of isolated, non-root Docker containers orchestrated via `docker-compose.prod.yml` behind Caddy / Nginx reverse proxy with automatic TLS certificate provision and renewal.

## Domain Routing Models

### Single Host Configuration
- `max.example/` -> Web Application (Module 35)
- `max.example/admin/` -> Admin Console (Module 37)
- `max.example/api/` -> MAX Backend API (Modules 01–33)

### Multi-Subdomain Configuration
- `app.max.example` -> Web Application
- `api.max.example` -> MAX API Gateway
- `admin.max.example` -> Admin Console

## Deployment Procedure

1. **Clone Repository on Remote Server**:
   ```bash
   git clone https://github.com/KoramYashwanthReddy/Max.git /opt/max
   cd /opt/max
   ```

2. **Configure Environment Secrets**:
   ```bash
   cp .env.production.example .env
   # Edit .env and set strong secrets for MAX_SECURITY__SECRET_KEY, DB passwords, etc.
   ```

3. **Run Automated Deployment Script**:
   ```bash
   chmod +x scripts/deploy.sh scripts/rollback.sh
   ./scripts/deploy.sh production
   ```

4. **Verify Deployment & Smoke Tests**:
   ```bash
   python scripts/smoke_test.py --host https://max.example
   ```

## Server Firewall Rules (UFW / iptables)
Only public web traffic should enter the server network:
- `ALLOW 80/tcp` (HTTP -> HTTPS redirect)
- `ALLOW 443/tcp` (HTTPS TLS traffic)
- `ALLOW 22/tcp` (SSH key-authenticated access)
- `DENY 5432/tcp` (PostgreSQL - Internal docker network only)
- `DENY 6379/tcp` (Redis - Internal docker network only)
- `DENY 9000/tcp` (MinIO - Internal docker network only)
