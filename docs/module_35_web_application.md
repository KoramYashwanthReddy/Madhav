# Module 35 — Web Application

## Overview
Module 35 implements the production-grade browser client interface for MAX. The web application acts strictly as a **client UI**, communicating with the Python backend API (Modules 01–34) without duplicating backend intelligence, reasoning, or security authorization logic in the browser.

## Architecture

```
                    MAX WEB APPLICATION
                             │
                  React 18 + TypeScript
                 Vite 6 + HSL CSS Tokens
                             │
                      HTTPS / REST API
                   (http://127.0.0.1:8000)
                             │
                             ▼
                    MAX PYTHON BACKEND
                             │
           ┌─────────────────┼─────────────────┐
           ↓                 ↓                 ↓
        AI Core           Memory             Tools
           ↓                 ↓                 ↓
       Reasoning            RAG               Agents
           │
           └─────────────────┬─────────────────┘
                             ↓
                     Permission Engine
```

## Directory Structure (`web/`)
- `web/package.json`: Dependencies (React 18, Lucide React, TypeScript 5.7, Vite 6).
- `web/vite.config.ts`: Proxy configuration to backend API server (`/api/v1` -> `http://127.0.0.1:8000/api/v1`).
- `web/src/styles/index.css`: Glassmorphism theme, dark mode palette, focus rings, accessibility styles, HSL CSS variables.
- `web/src/types/index.ts`: TypeScript definitions matching backend DTOs (Health, Chat, Tasks, Automations, Memory, Knowledge, Agents, Tools, Integrations, Audit, Evaluation, System, Approvals).
- `web/src/api/client.ts`: Production REST API client with fallback simulation for offline browser mode.
- `web/src/context/WebAppContext.tsx`: Global React Context managing navigation, notifications, health status, and security approvals.
- `web/src/components/`:
  - `Header.tsx`: Navigation header with backend status indicator, quick command launcher, theme toggle, and notification bell.
  - `Sidebar.tsx`: Navigation sidebar with unread/status badges for all 14 primary sections.
  - `QuickCommandPalette.tsx`: Global search modal (`Ctrl+K`) for jumping across sections and quick prompt execution.
  - `ApprovalModal.tsx`: Module 15 security approval modal for human-in-the-loop authorization.
  - `NotificationDrawer.tsx`: Slide-out panel for proactive alerts and event logs.
- `web/src/views/`:
  1. `HomeView.tsx`: Dashboard overview with metric cards and workspace quick launchers.
  2. `ChatView.tsx`: Conversational AI interface with streaming responses, model selection, execution steps, and voice toggle.
  3. `TasksView.tsx`: Task management dashboard displaying multi-agent step progress and goal creation.
  4. `AutomationsView.tsx`: Scheduler workspace for cron triggers, job toggles, and execution logs.
  5. `MemoryView.tsx`: Memory query engine for facts, preferences, importance scores, and tag filters.
  6. `KnowledgeView.tsx`: Personal Knowledge graph visualizer displaying node entities and relationship edges.
  7. `AgentsView.tsx`: Specialized AI agent manager displaying agent status and capability tags.
  8. `ToolsView.tsx`: Tool Registry Sandbox showing required parameters and security approval flags.
  9. `IntegrationsView.tsx`: External connector dashboard showing auth states and sync times.
  10. `NotificationsView.tsx`: Proactive notification center with categories and mark-as-read functionality.
  11. `ActivityView.tsx`: Observability & audit log viewer displaying severity levels and module origins.
  12. `EvaluationsView.tsx`: Benchmark quality dashboard with faithfulness, relevance, precision, and safety scores.
  13. `SystemView.tsx`: Real-time system telemetry displaying CPU load, memory usage, and provider latencies.
  14. `SettingsView.tsx`: Configuration workspace for autonomy levels (Strict, Guarded, Autonomous) and accessibility options.

## Verification
- Web application compiled cleanly using `tsc && vite build` with 0 errors.
- Python pytest suite passed with 830 passing tests.
