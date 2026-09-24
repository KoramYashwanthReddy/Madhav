# Module 37 — Admin / System Console

## Overview
Module 37 implements the high-privilege enterprise administrative console (`MAX SYSTEM CONSOLE`) for MAX. Built as a separate architectural client UI, it connects to the authoritative Python backend (Modules 01–36) to allow system operators and administrators to monitor, diagnose, and inspect system operational health, AI runtimes, agent state, tool execution policies, device registrations, audit streams, and security boundaries.

## Architecture

```
                MAX CORE
                   │
       ┌───────────┼───────────┐
       │           │           │
       ▼           ▼           ▼
    Desktop       Web        Mobile
     34            35          36
       │
       │
       ▼
 Admin/System Console
       37
```

## Directory Structure (`admin/`)
- `admin/package.json`: React 18, Lucide React, TypeScript 5.7, Vite 6 dependencies.
- `admin/vite.config.ts`: Proxy configuration (`/api/v1/admin` -> `http://127.0.0.1:8000/api/v1/admin`).
- `admin/src/styles/index.css`: Enterprise technical dark design system, data tables, ARIA focus rings, status badges.
- `admin/src/utils/redactSecrets.ts`: Automatic secret redaction utility redacting passwords, tokens, API keys, authorization headers, cookies, and credentials in audit/log displays.
- `admin/src/types/index.ts`: TypeScript DTO definitions for all 17 administrative sections, Admin Roles (`SUPER_ADMIN`, `SYSTEM_ADMIN`, `OPERATOR`, `READ_ONLY_ADMIN`), and Security Modes (`NORMAL`, `RESTRICTED`, `LOCKDOWN`, `MAINTENANCE`).
- `admin/src/api/admin/client.ts`: Typed Admin REST API client with header authentication, secret redaction, safe error handling (never exposing backend stack traces), and mock fallback simulation.
- `admin/src/context/AdminContext.tsx`: React Context managing console state, security modes, read-only mode, global search, emergency kill switch, and dangerous action modals.
- `admin/src/components/`:
  - `AdminHeader.tsx`: Header displaying console title, security mode badge, emergency kill switch trigger, global search bar (`Ctrl+K`), and admin role pill.
  - `AdminSidebar.tsx`: Enterprise navigation sidebar listing all 17 sections.
  - `KillSwitchModal.tsx`: Deliberate confirmation modal for emergency lockdown with warning consequences.
  - `DangerousActionModal.tsx`: Double-confirmation dialog for destructive administrative actions (device revocation, data deletion).
  - `GlobalSearchModal.tsx`: Server-side search modal searching across tasks, agents, tools, devices, audit events, traces, and models.
- `admin/src/views/` (17 Primary Workspaces):
  1. `DashboardView.tsx`: Executive operational dashboard displaying component health matrix, alerts, and quick section jumps.
  2. `RuntimeView.tsx`: AI Runtime inspection (Module 04) showing request counts, token processing throughput, and provider latencies.
  3. `ModelsView.tsx`: Model Management (Module 05) displaying model versions, checksums, and lifecycle activation controls.
  4. `AgentsView.tsx`: Agent Engine monitor (Module 13) displaying status, capabilities, and pause/resume/restart controls.
  5. `ToolsView.tsx`: Tool Registry explorer (Module 14) displaying parameter schemas, risk levels, and approval requirements.
  6. `SecurityView.tsx`: Security Engine console (Module 15) displaying security mode (`NORMAL`/`RESTRICTED`/`LOCKDOWN`/`MAINTENANCE`), active policies, violation logs, and kill switch trigger.
  7. `TasksView.tsx`: Task Engine monitor (Module 12) displaying task priority, progress percentage, and status.
  8. `AutomationsView.tsx`: Scheduler workspace (Module 28) displaying cron triggers and job statuses.
  9. `DevicesView.tsx`: Client Device & Session manager (Modules 34, 35, 36) displaying platform details and device revocation controls.
  10. `IntegrationsView.tsx`: External Integrations hub (Module 29) displaying provider connectivity and auth statuses.
  11. `NotificationsView.tsx`: Notification delivery monitor (Module 27) displaying channel health.
  12. `ObservabilityView.tsx`: Observability console (Module 33) with distinct tabs for Logs, Metrics, and Distributed Trace timeline visualizer.
  13. `AuditView.tsx`: Audit Explorer (Module 33) with multi-field search and automatic secret redaction.
  14. `EvaluationsView.tsx`: Evaluation System dashboard (Module 32) displaying faithfulness, relevance, precision, and safety scores.
  15. `ConfigurationView.tsx`: Safe Configuration viewer (Module 02) displaying environment variables with redacted secrets.
  16. `DiagnosticsView.tsx`: Predefined safe diagnostics suite running automated component capability checks.
  17. `SettingsView.tsx`: Admin console preferences, session role context selector, and read-only mode toggle.

## Verification
- Admin Console compiled cleanly using `tsc && vite build` with 0 errors.
- All 17 administrative workspaces, security controls, emergency kill switch, and secret redactions verified.
