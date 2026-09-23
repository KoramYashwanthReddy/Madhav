# Module 12 — Task Engine Documentation

## Executive Overview

The **Task Engine** (Module 12) is the task management layer of the Madhav personal AI assistant runtime.

Module 11 (**Reasoning & Planning**) answers:
> *"What should happen?"* (Formulating goals, steps, dependencies, constraints, and plans)

Module 12 (**Task Engine**) answers:
> *"What individual tasks represent that plan and what is their lifecycle state?"*

---

## CRITICAL ARCHITECTURAL BOUNDARY RULE

> **MODULE 12 MANAGES TASKS. MODULE 12 DOES NOT EXECUTE TASKS.**

The Task Engine **NEVER** performs shell commands, terminal execution, filesystem operations, browser control, email sending, calendar operations, API calls, tool selection, or agent execution. Starting a task (`status -> IN_PROGRESS`) updates lifecycle metadata only. Active execution belongs to future modules (Module 13+).

---

## Core Domain Models

### Task Entity (`Task`)
Represents one unit of work:
- **`id`**: `task_...`
- **`owner_id`**: User ID
- **`title`**: Descriptive title
- **`description`**: Detailed task description
- **`type`**: `GENERAL`, `RESEARCH`, `ANALYSIS`, `CODING`, `WRITING`, `REVIEW`, `PLANNING`, `MAINTENANCE`, `PERSONAL`, `SYSTEM`, `OTHER`
- **`status`**: `PENDING`, `READY`, `BLOCKED`, `IN_PROGRESS`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `EXPIRED`, `SKIPPED`
- **`priority`**: `LOW` (rank 0), `NORMAL` (rank 1), `HIGH` (rank 2), `URGENT` (rank 3), `CRITICAL` (rank 4)
- **`progress`**: Percentage integer (0 to 100)
- **`source`**: `USER`, `CONVERSATION`, `PLAN`, `REASONING`, `SYSTEM`, `IMPORTED`, `MANUAL`, `FUTURE_AGENT`
- **`plan_id`**, **`plan_version`**, **`plan_step_id`**: Traceability pointers to Module 11 plans
- **`parent_task_id`**: Hierarchical parent subtask pointer
- **`group_id`**: Assigned `TaskGroup` identifier
- **`schedule`**: Schedule timing metadata (`scheduled_at`, `due_at`, `timezone`, `recurrence`)
- **`result`**, **`failure`**: Outcome diagnostic metadata
- **`retry_count`**, **`max_retries`**, **`retryable`**: Control metadata for retries

---

## State Machine & Valid Transitions

Transitions are validated by `TaskStateMachine`:
- `PENDING` $\rightarrow$ `READY`, `BLOCKED`, `IN_PROGRESS`, `PAUSED`, `CANCELLED`, `SKIPPED`
- `READY` $\rightarrow$ `IN_PROGRESS`, `PAUSED`, `BLOCKED`, `CANCELLED`, `SKIPPED`
- `BLOCKED` $\rightarrow$ `READY`, `PENDING`, `CANCELLED`, `SKIPPED`
- `IN_PROGRESS` $\rightarrow$ `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `SKIPPED`
- `PAUSED` $\rightarrow$ `IN_PROGRESS`, `CANCELLED`, `SKIPPED`
- `FAILED` $\rightarrow$ `READY` (via explicit retry/reset), `CANCELLED`, `SKIPPED`
- `COMPLETED`, `CANCELLED`, `EXPIRED`, `SKIPPED` $\rightarrow$ Terminal states

---

## Plan-to-Task Conversion (`PlanTaskMapper`)

The `PlanTaskMapper` transforms Module 11 `Plan` objects into `Task` entities and `TaskDependency` graph edges:
1. **Traceability**: Retains links to `plan_id`, `plan_version`, `plan_step_id`, and `reasoning_id`.
2. **Idempotency**: Prevents duplicate task generation if conversion is executed multiple times for the same plan version.

---

## Dependency & Cycle Validation (`TaskValidator`)

- **Dependencies**: Directed edges (`DEPENDS_ON`, `BLOCKS`, `RELATED_TO`).
- **DFS Cycle Detection**: Rejects cyclic dependencies ($A \rightarrow B \rightarrow C \rightarrow A$) via `CircularTaskDependencyError`.
- **Parent/Child Hierarchy**: Prevents self-parenting and nesting loops ($Child \rightarrow Parent \rightarrow Child$) via `TaskHierarchyError`.

---

## REST API Reference

### Tasks
- `POST /api/v1/tasks` — Create task
- `GET /api/v1/tasks` — List tasks (supports filtering, sorting, and pagination)
- `GET /api/v1/tasks/{task_id}` — Retrieve task
- `PATCH /api/v1/tasks/{task_id}` — Update task
- `DELETE /api/v1/tasks/{task_id}` — Delete task

### Lifecycle Control
- `POST /api/v1/tasks/{task_id}/start` — Move status to `IN_PROGRESS`
- `POST /api/v1/tasks/{task_id}/pause` — Move status to `PAUSED`
- `POST /api/v1/tasks/{task_id}/resume` — Move status to `IN_PROGRESS`
- `POST /api/v1/tasks/{task_id}/complete` — Move status to `COMPLETED`
- `POST /api/v1/tasks/{task_id}/cancel` — Cancel task and child subtasks
- `POST /api/v1/tasks/{task_id}/retry` — Reset `FAILED` task to `READY`
- `PATCH /api/v1/tasks/{task_id}/progress` — Update progress (0–100%)

### Dependencies & Readiness
- `POST /api/v1/tasks/{task_id}/dependencies` — Add task dependency
- `GET /api/v1/tasks/{task_id}/dependencies` — List dependencies
- `DELETE /api/v1/tasks/{task_id}/dependencies/{dependency_id}` — Delete dependency
- `GET /api/v1/tasks/{task_id}/readiness` — Evaluate task readiness

### Groups & Plan Conversion
- `POST /api/v1/task-groups` — Create task group
- `GET /api/v1/task-groups/{group_id}/summary` — Aggregate progress metrics
- `POST /api/v1/plans/{plan_id}/tasks` — Convert Module 11 plan steps into tasks
