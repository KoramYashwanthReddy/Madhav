# Module 15 — Permission & Security Layer

## 1. Purpose

The **Permission & Security** subsystem provides the security boundary for the Max Personal AI runtime. Situated strictly between the Agent / Tool Registry layer (Modules 13 & 14) and future Execution modules (Modules 16+), it answers the fundamental security question:

> **"Is this specific requested action allowed?"**

Max enforces permissions **BEFORE** any real-world action occurs.

---

## 2. Core Security Philosophy

1. **DEFAULT DENY**: Unless an explicit policy or active grant permits an action, the decision is **DENIED** with reason `NO_POLICY_MATCH`.
2. **NO LLM AUTHORIZATION**: Permission decisions are 100% policy-based, deterministic, and auditable. AI outputs may request actions, but NEVER authorize them.
3. **FAIL-CLOSED**: If an error or exception occurs during evaluation, the system defaults to **DENIED** / **BLOCKED** with status `ERROR`.
4. **NO REAL EXECUTION**: Module 15 issues an `AuthorizedExecutionRequest` contract for future modules but does NOT perform filesystem, terminal, or network execution.

---

## 3. Architecture & Data Flow

```
Agent / Tool Registry Request
             │
             ▼
    SecurityContextBuilder
             │
             ▼
       PermissionGate
             │
             ├──────────────────────────────────────┐
             ▼                                      ▼
    PermissionEvaluator                    EmergencyBlock / KillSwitch
  (Precedence Rules:                        (Global lockdown check)
   1. Emergency DENY
   2. Explicit DENY
   3. Security Mode DENY
   4. Owner Mismatch DENY
   5. Active Permission Grants
   6. Explicit Policy Rules
   7. Default DENY)
             │
             ├───────────────────────┬───────────────────────┐
             ▼                       ▼                       ▼
      [Status: ALLOWED]      [Status: REQUIRES_APPROVAL]   [Status: DENIED/BLOCKED]
             │                       │                       │
             ▼                       ▼                       ▼
  AuthorizedExecutionRequest  ApprovalRequest (PENDING)   SecurityAuditLog & Event
```

---

## 4. Policy Evaluation Precedence

Deterministic policy evaluation follows a strict, non-overridable order:

1. **Emergency DENY**: Active kill-switch overrides all rules -> `BLOCKED`, `EMERGENCY_BLOCK`.
2. **Security Mode DENY**: Operational security modes (e.g. `LOCKDOWN` mode blocks HIGH/CRITICAL risk actions) -> `BLOCKED`, `SECURITY_MODE_BLOCKED`.
3. **Owner Boundary DENY**: Principal owner mismatch against target resource owner -> `DENIED`, `OWNER_MISMATCH`.
4. **Active Permission Grants**: Unexpired temporary or persistent grants -> `ALLOWED` or `REQUIRES_APPROVAL`.
5. **Policy Rules Match**: Evaluates enabled policy rules ordered by policy priority and rule priority -> `EXPLICIT_DENY`, `EXPLICIT_ALLOW`, or `APPROVAL_REQUIRED`.
6. **Default DENY**: Unmatched requests default to -> `DENIED`, `NO_POLICY_MATCH`.

---

## 5. Security Modes

Operational security modes configured via `SecurityModeService`:

- **`NORMAL`**: Standard policy evaluation.
- **`RESTRICTED`**: Requires explicit human approval for HIGH and CRITICAL risk actions even if policies permit them.
- **`LOCKDOWN`**: Immediately blocks all HIGH and CRITICAL risk actions.
- **`MAINTENANCE`**: System operational maintenance; external actions blocked.

---

## 6. Key Domain Interfaces & Services

- **`PermissionGate`**: Primary check interface `check(request)` and `check_and_authorize(request)`.
- **`PermissionEvaluator`**: Core deterministic evaluation engine.
- **`PolicyService`**: CRUD management for permission policies and version tracking.
- **`ApprovalService`**: Lifecycle management for human approval requests (`PENDING`, `APPROVED`, `DENIED`, `EXPIRED`, `CANCELLED`).
- **`PermissionGrantService`**: Manages temporary/persistent grants (`ONE_TIME`, `SESSION`, `TIME_LIMITED`, `PERSISTENT`) and instant revocation.
- **`KillSwitchService`**: Emergency block activation and status monitoring.
- **`SecurityAuditService` & `SecurityViolationService`**: Immutable audit event logging and boundary violation tracking.
- **`AuthorizedExecutionRequest`**: Token boundary contract presented to future execution modules (Modules 16+).

---

## 7. API Endpoints (`/api/v1/security/*`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/security/permissions/check` | Evaluate permission for requested action |
| `GET` | `/api/v1/security/policies` | List permission policies |
| `POST` | `/api/v1/security/policies` | Create a new permission policy |
| `GET` | `/api/v1/security/policies/{id}` | Get policy details by ID |
| `PATCH` | `/api/v1/security/policies/{id}` | Update policy rules or status |
| `DELETE` | `/api/v1/security/policies/{id}` | Delete policy by ID |
| `GET` | `/api/v1/security/approvals` | List approval requests |
| `POST` | `/api/v1/security/approvals/{id}/approve` | Approve a pending request |
| `POST` | `/api/v1/security/approvals/{id}/deny` | Deny a pending request |
| `POST` | `/api/v1/security/grants` | Issue a permission grant |
| `POST` | `/api/v1/security/grants/{id}/revoke` | Revoke an active grant |
| `GET` | `/api/v1/security/mode` | Query security mode state |
| `POST` | `/api/v1/security/mode` | Set security mode state |
| `GET` | `/api/v1/security/emergency` | Query emergency kill-switch status |
| `POST` | `/api/v1/security/emergency/activate` | Activate emergency block |
| `POST` | `/api/v1/security/emergency/deactivate` | Deactivate emergency block |
| `GET` | `/api/v1/security/events` | Query audit log security events |
| `GET` | `/api/v1/security/violations` | Query security violation records |

---

## 8. Threat Model & Mitigations

- **Prompt Injection**: AI models cannot bypass permission evaluation because evaluation is deterministic and policy-based outside the LLM context.
- **Confused Deputy**: Agent capabilities do not automatically grant permissions; every request is checked independently against owner boundaries.
- **Path Traversal**: Resource paths are normalized (`normalize_path`) to prevent `../` directory traversal attempts before evaluation.
- **Stale Grants**: Grants feature automatic expiration (`expires_at`) and support instant revocation without service restart.
