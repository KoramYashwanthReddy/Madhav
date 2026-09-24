# Module 34 — Desktop Application

## Purpose & Overview

Module 34 implements the native Windows desktop client application for MAX. It provides a rich, modern, glassmorphic desktop user interface connected to the MAX Python backend (Modules 01–33).

The desktop application is **NOT the AI brain** — the Python backend retains sole authority for AI runtime execution, reasoning, memory, RAG, tool orchestration, permissions, automation, integrations, evaluation, and observability.

---

## Core Architecture

```
                    MAX DESKTOP APPLICATION
                         │
          ┌──────────────┴──────────────┐
          │                             │
      React UI                     Tauri/Rust
  (TypeScript/Vite)               (Native Shell)
          │                             │
          └──────────────┬──────────────┘
                         │
                  Secure IPC / REST API
                         │
                         ▼
                 MAX Python Backend
```

- **Tauri / Rust (`desktop/src-tauri`)**:
  - Native window management (Frameless Quick HUD overlay, resizable main workspace).
  - Background Python backend process lifecycle manager (`start_backend_process`, `stop_backend_process`).
  - Native system tray integration & global shortcut support (`Alt+Space` for HUD toggle).
  - Host OS & hardware telemetry monitoring (`get_system_info`).

- **React / TypeScript / Vite (`desktop/src`)**:
  - **Conversation View**: Interactive chat workspace, streaming messages, reasoning breakdown accordions, tool invocation badges, model selector.
  - **Task & Agent Workspace**: Active tasks, subtasks, agent execution status, delegation visualizer.
  - **Memory & Knowledge Hub**: Learned preferences, profile memories, RAG vector retrieval workbench.
  - **Automations & Scheduler**: Cron background jobs, proactive candidate notifications.
  - **Integrations & Developer Tools**: GitHub, Web Intelligence, Terminal/Filesystem/Browser session monitors.
  - **Evaluation System**: Quality benchmark suites, LLM judge reports, regression delta metrics.
  - **Observability & Audit Dashboard**: Real-time execution traces, step-by-step timelines, metric graphs, append-only security audit log viewer.
  - **Settings & Autonomy**: Autonomy level slider (0=Observe, 1=Notify, 2=Recommend, 3=Task, 4=Action, 5=Workflow), backend connection settings, system specs.
  - **Quick HUD Overlay**: Floating Command Bar for instant query entry and quick commands.
  - **Security Approval Modal**: Module 15 authorization request popups with risk severity badges and action countdown timers.

---

## Tauri IPC Commands & API Bridges

| Tauri Command / Bridge | Description |
|---|---|
| `check_backend_status` | Asynchronously pings Python backend `/api/v1/observability/health` |
| `start_backend_process` | Spawns `python -m max.main` background process if inactive |
| `stop_backend_process` | Gracefully terminates spawned backend process |
| `toggle_overlay_window` | Shows/hides the Quick HUD Overlay (`max-overlay`) |
| `get_system_info` | Retrieves host OS, CPU thread count, and memory metrics |
