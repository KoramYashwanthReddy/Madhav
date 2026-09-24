# Production Security Hardening & Zero-Trust Architecture

## Security Principles

1. **Non-Root Execution**:
   All container images (`Dockerfile.backend`, `Dockerfile.worker`, `Dockerfile.scheduler`, `Dockerfile.web`, `Dockerfile.admin`) execute as unprivileged user `maxuser` (UID 10001 / GID 10001).

2. **No Docker Socket Mounting**:
   `docker.sock` is never mounted inside application containers.

3. **Restricted Filesystem**:
   Production container filesystems operate in read-only mode with explicit temporary mounts (`/tmp/max`, `/app/logs`). Host filesystem mounts (like `/:/host`) are strictly forbidden.

4. **Secret Protection & Redaction**:
   Production secrets (database connection strings, API tokens, signing keys) are injected via environment variables or Docker Secrets. All infrastructure logging channels automatically redact key fields (`database_url`, `secret_key`, `api_key`).

5. **Security Headers Enforced**:
   - `Content-Security-Policy: default-src 'self'`
   - `X-Frame-Options: SAMEORIGIN`
   - `X-Content-Type-Options: nosniff`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Referrer-Policy: strict-origin-when-cross-origin`

6. **Strict CORS Policy**:
   Wildcard origins (`*`) are prohibited when credentials are enabled. Allowed origins are explicitly loaded from `MAX_CORS__ALLOWED_ORIGINS`.
