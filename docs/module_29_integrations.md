# Module 29 — External Integrations Architecture & Design Specification

## Overview

Module 29 (`src/max/integrations`) provides a provider-neutral, security-first External Integration Framework for the MAX Personal AI system. It empowers MAX to securely interface with external third-party services (such as Email, Calendar, Cloud Storage, Developer tools, and Webhooks) while maintaining strict isolation, secret protection, permission enforcement, and auditability.

```
External Services (Email, Calendar, GitHub, Webhooks)
       ▲
       │ (REST / Webhooks)
       ▼
Module 29 — External Integrations Engine
 ├── IntegrationRegistry (Capability Discovery & Provider Management)
 ├── SecretStore (Secure Credential Storage Boundary)
 ├── ConnectionService (Lifecycle: PENDING -> ACTIVE -> DEGRADED -> REVOKED)
 ├── IntegrationExecutionService (Rate-Limit, Retries, Idempotency, Dry-Run)
 ├── OAuth2Handler (CSRF State Token Validation & Token Refresh)
 └── WebhookService (HMAC Validation, Replay Protection, Normalization)
       │
 ┌─────┴─────────────────────────┬───────────────────────────┬────────────────────────┐
 ▼                               ▼                           ▼                        ▼
Module 14 Tool Registry    Module 15 Permission Gate   Module 27 Notification  Module 28 Scheduler
(Auto-registered Tools)    (Authoritative Security)    (Status & Approvals)    (External Events)
```

---

## Architectural Principles & Scope Boundaries

Module 29 is an **Integration Framework** responsible for answering:
> *"How does MAX securely communicate with an external service?"*

It explicitly defers core responsibilities to dedicated MAX modules:
- **Module 15**: Authoritative permission decision (`PermissionGate.check`).
- **Module 14**: Tool definition discovery and registration (`ToolRegistryService`).
- **Module 27**: User notifications for status changes, auth expirations, and approvals (`NotificationService`).
- **Module 28**: Scheduling and automation triggers (`ScheduleEvent` & `AutomationEngine`).

---

## Domain Entity Model

- **`Integration`**: High-level metadata definition of an external service.
- **`IntegrationProvider`**: Adapter interface exposing available capabilities (`ExternalIntegrationProvider`).
- **`IntegrationConnection`**: Authenticated account connection instance owned by a specific user.
- **`CredentialReference`**: Opaque reference (`cred_...`) pointing to raw tokens/keys in `SecretStore`. **Never stores raw secrets.**
- **`IntegrationCapability`**: Provider-exposed capability (e.g., `email.send`, `calendar.create_event`).
- **`IntegrationAction`**: Callable structured action with input/output JSON schemas and risk levels.
- **`RiskLevel`**: Security classification (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **`WebhookSubscription`**: Subscription record for incoming provider webhooks.
- **`WebhookEvent`**: Raw ingested webhook payload event log.
- **`ExternalEvent`**: Normalized, sanitized event emitted to Module 28 Scheduler.

---

## Secret Storage Boundary (`SecretStore`)

Raw credentials (API keys, access tokens, refresh tokens, client secrets) are **strictly isolated** within the `SecretStore` subsystem and never appear in domain objects, exceptions, API responses, or logs.

- **Interface**: `SecretStore` (`store`, `retrieve`, `delete`, `rotate`, `exists`).
- **Development/Testing**: `InMemorySecretStore` thread-safe in-memory store.
- **Redaction**: Custom string representations default to `<InMemorySecretStore [REDACTED]>`.

---

## Provider Adapters & Mock Implementations

Module 29 ships with deterministic mock providers:
1. `MockEmailProvider` (`mock_email`): `email.send`, `email.read`, `email.search`
2. `MockCalendarProvider` (`mock_calendar`): `calendar.list_events`, `calendar.create_event`, `calendar.update_event`, `calendar.delete_event`
3. `MockStorageProvider` (`mock_storage`): `storage.list`, `storage.read`, `storage.upload`, `storage.delete`
4. `MockGitHubProvider` (`mock_github`): `repository.read`, `issue.create`, `pull_request.read`
5. `MockWebhookProvider` (`mock_webhook`): `webhook.emit` with HMAC SHA256 signature verification.

---

## Connection Lifecycle State Machine

```
   [CONNECT] ──> PENDING ──> ACTIVE ───> DEGRADED (Health check warning)
                               │
                               ├──> EXPIRED (OAuth token refresh required)
                               ├──> DISCONNECTED (User voluntary disconnect)
                               └──> REVOKED (Security revocation)
```

---

## OAuth2 Security & CSRF State Validation

- `OAuth2Handler.generate_authorization_url`: Generates a cryptographically random, single-use state token (`secrets.token_urlsafe(32)`).
- `OAuth2Handler.validate_state`: Enforces expiration time windows (default 10 minutes) and single-use consumption to prevent CSRF attacks.

---

## Execution Pipeline

1. **Idempotency Check**: Retries carrying the same `idempotency_key` return cached responses without executing duplicate side-effects.
2. **Connection Status Check**: Verifies status is `ACTIVE` or `DEGRADED`.
3. **Rate Limiting**: Enforces sliding-window rate ceilings (default 60 req/min).
4. **Module 15 Security Evaluation**: Passes every request through `PermissionGate`.
   - `ALLOWED`: Proceed.
   - `REQUIRE_APPROVAL`: Pauses execution, returns status `REQUIRES_APPROVAL`, and dispatches notification.
   - `DENIED`: Rejects request immediately.
5. **Dry-Run Mode**: Returns execution plan without invoking external side-effects if `dry_run=True`.
6. **Execution & Audit Logging**: Invokes provider adapter, records latency, and logs audit events (redacting secrets).

---

## Webhook Processing & Prompt Injection Defense

1. **Payload Size Ceiling**: Rejects payloads exceeding limit (default 1MB).
2. **Deduplication**: Hashes payload content (`SHA256`) to reject duplicate events.
3. **Signature Validation**: HMAC SHA256 signature verification via provider `handle_webhook`.
4. **Prompt Injection Defense**: External payload content is treated as **UNTRUSTED DATA** and never evaluated as code or system instructions (`eval()` / `exec()` prohibited).
5. **Event Emission**: Normalizes into `ExternalEvent` and emits directly into Module 28 Scheduler.

---

## REST API Endpoints

### Integrations & Capabilities
- `GET /api/v1/integrations` — List integrations
- `GET /api/v1/integrations/{integration_id}` — Get integration metadata
- `GET /api/v1/integrations/{integration_id}/capabilities` — Discover capabilities

### Connections & Execution
- `POST /api/v1/integrations/connections` — Create connection
- `GET /api/v1/integrations/connections` — List owner connections
- `GET /api/v1/integrations/connections/{connection_id}` — Connection details
- `POST /api/v1/integrations/connections/{connection_id}/health` — Health check
- `POST /api/v1/integrations/connections/{connection_id}/disconnect` — Disconnect connection
- `POST /api/v1/integrations/connections/{connection_id}/revoke` — Revoke connection
- `POST /api/v1/integrations/connections/{connection_id}/actions/{action_id}` — Execute action

### OAuth2 Flow
- `POST /api/v1/integrations/oauth/url` — Generate authorization URL
- `POST /api/v1/integrations/oauth/callback` — Handle callback code exchange

### Webhooks
- `POST /api/v1/webhooks/subscribe` — Create webhook subscription
- `POST /api/v1/webhooks/{subscription_id}/unsubscribe` — Cancel subscription
- `POST /api/v1/webhooks/{integration_id}` — Ingest incoming webhook
