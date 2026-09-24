# Module 38 — Infrastructure & Production Deployment

## Core Summary
Module 38 implements provider-neutral, production-grade infrastructure for the MAX Personal AI Operating System. It provides complete environment orchestration across Local Development (Target 1), Local Production-Like (Target 2), Remote Personal Server (Target 3), and Future Cloud (Target 4).

## System Components Implemented
- **Docker Multi-Stage Build Architecture**: Production `Dockerfile.backend`, `Dockerfile.worker`, `Dockerfile.scheduler`, `Dockerfile.web`, `Dockerfile.admin` running as non-root user `maxuser` (UID 10001).
- **Docker Compose Orchestration**: Development (`docker-compose.dev.yml`) and production-like (`docker-compose.prod.yml`) stack definitions with network segmentation (`max-public`, `max-app`, `max-data`).
- **Reverse Proxy Architecture**: Caddy (`Caddyfile`) and Nginx (`nginx.conf`) with automatic TLS, HTTPS redirect, HSTS, security headers, CORS protection, rate limiting, and SSE/WebSocket streaming buffer bypass.
- **Data & Storage Infrastructure**: PostgreSQL 16 connection management and init scripts (`init.sql`), Redis 7 caching/locking management, MinIO object storage client and bucket initialization (`minio-init.sh`).
- **Secret Management Architecture**: Environment/Docker Secrets provider resolution, secret rotation audit tracking, and automated log redaction.
- **CI/CD Pipeline**: GitHub Actions workflows (`ci.yml`, `deploy.yml`) covering linting, typechecking, pytest test execution, static frontend compilation, Docker image vulnerability scanning, and automated deployment verification.
- **Operational Automation & Smoke Tests**: Automated deployment script (`deploy.sh`), emergency rollback script (`rollback.sh`), and end-to-end Python smoke test suite (`smoke_test.py`).
- **SRE Documentation & Runbooks**: Comprehensive architecture, security hardening, local development, production deployment, and incident response documentation (`docs/infrastructure/`).
