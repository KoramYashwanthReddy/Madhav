# Module 28 — Scheduler & Automation Engine

## Overview

Module 28 is the provider-neutral, deterministic **Scheduler & Automation Engine** for MAX (Personal AI Assistant runtime).

The Scheduler acts as an **ORCHESTRATOR**. It answers:
- **WHEN** should an action or workflow happen?
- **WHY** should it happen (trigger/event/condition)?
- **WHAT** automation workflow should be executed?

It relies on existing MAX modules to handle execution details:
- **Module 12 (Task Engine)**: What task needs to be performed
- **Module 13 (Agent Engine)**: Who performs the task
- **Module 14 (Tool Registry)**: What tool performs the step
- **Module 15 (Permission & Security)**: Is the action allowed
- **Module 27 (Notification System)**: How notifications are delivered

---

## Domain Architecture & Core Entities

1. **Schedule**: Represents *WHEN* an automation should run (`ONE_TIME`, `RECURRING`, `CRON`, `INTERVAL`, `EVENT`, `CONDITIONAL`).
2. **Automation**: Represents *WHAT* workflow pipeline should run (Triggers -> Conditions -> Steps -> Tasks/Agents/Tools -> Verification -> Notifications).
3. **Trigger**: Defines the activation mechanism (`TIME_TRIGGER`, `INTERVAL_TRIGGER`, `CRON_TRIGGER`, `EVENT_TRIGGER`, `CONDITION_TRIGGER`, `MANUAL_TRIGGER`).
4. **Execution**: Tracks a single run of an automation step-by-step with complete audit history and idempotency key.
5. **AutomationStep**: Structured step (`CREATE_TASK`, `WAIT`, `CHECK_CONDITION`, `ASSIGN_AGENT`, `EXECUTE_TOOL`, `VERIFY_RESULT`, `SEND_NOTIFICATION`).
6. **RecurrenceRule**: Specifies complex recurrence rules (Frequency, Interval, ByDay, ByMonthDay, ByMonth, StartAt, EndAt, Count, TimeZone).
7. **SchedulerLock**: Distributed lock entity preventing concurrent duplicate runs of the same schedule.

---

## Lifecycle State Machines

### Schedule & Automation States

```
[ DRAFT ] ───> [ SCHEDULED ] <───> [ PAUSED ]
                     │                   │
                     ▼                   ▼
                  [ READY ] ───> [ CANCELLED ]
                     │
                     ▼
                 [ RUNNING ] ───> [ FAILED ]
                     │
                     ▼
                [ COMPLETED ] ───> [ EXPIRED ]
```

State transitions are validated deterministically via `validate_schedule_transition` and `validate_automation_transition`. Invalid transitions raise `InvalidStateTransitionError`.

---

## Timezone & Cron Handling

- **IANA Timezones**: Schedules support all IANA time zones (e.g., `Asia/Kolkata`, `America/New_York`, `Europe/London`, `UTC`) using Python's native `zoneinfo`.
- **DST & Local Time**: Local timezone intent is preserved while internal execution math converts cleanly to UTC datetimes.
- **Cron Engine**: Supports standard 5-part cron syntax (`minute hour day_of_month month day_of_week`).

---

## Misfire Policies & Concurrency Control

- **Misfire Policies**:
  - `SKIP`: Skip missed execution window and recalculate next run.
  - `RUN_ONCE`: Execute missed job once immediately, then resume normal schedule.
  - `RUN_IMMEDIATELY`: Immediately execute missed job.
  - `CATCH_UP`: Process all missed intervals sequentially.
- **Concurrency Policies**:
  - `FORBID`: Block new executions if an instance is already running.
  - `ALLOW`: Allow concurrent runs.
  - `REPLACE`: Cancel running execution and start new execution.
  - `QUEUE`: Queue new execution behind active execution.

---

## Security & Module Integrations

- **Module 15 (Permission Gate)**: MANDATORY AUTHORITATIVE GATE! Every automated action evaluates `PermissionGate.check(...)`.
  - `ALLOW`: Proceed with step execution.
  - `DENY`: Fail execution, log security decision, notify user.
  - `REQUIRE_APPROVAL`: Pause execution at step (`status = PAUSED`), record approval request ID, notify user via Module 27. When approved, execution resumes.
- **No `eval()` or `exec()`**: Conditions are evaluated using structured comparison operators (`EQUALS`, `GREATER_THAN`, `CONTAINS`, `MATCHES_REGEX`) without dynamic code execution.
- **Circuit Breaker**: Automations failing N consecutive times (`circuit_breaker_threshold`) are automatically disabled (`status = DISABLED`).
- **Dry-Run Mode**: Generates execution plan preview and permission evaluation without triggering external side effects.

---

## API Endpoints

### `/api/v1/scheduler`
- `POST /api/v1/scheduler`: Create schedule
- `GET /api/v1/scheduler`: List schedules
- `GET /api/v1/scheduler/{schedule_id}`: Get schedule
- `PUT /api/v1/scheduler/{schedule_id}`: Update schedule
- `POST /api/v1/scheduler/{schedule_id}/pause`: Pause schedule
- `POST /api/v1/scheduler/{schedule_id}/resume`: Resume schedule
- `POST /api/v1/scheduler/{schedule_id}/cancel`: Cancel schedule
- `DELETE /api/v1/scheduler/{schedule_id}`: Delete schedule
- `POST /api/v1/scheduler/{schedule_id}/trigger`: Trigger schedule manually
- `GET /api/v1/scheduler/{schedule_id}/next-run`: Get next run timestamp
- `GET /api/v1/scheduler/{schedule_id}/status`: Get schedule status
- `GET /api/v1/scheduler/executions`: List execution history

### `/api/v1/automations`
- `POST /api/v1/automations`: Create automation
- `GET /api/v1/automations`: List automations
- `GET /api/v1/automations/{automation_id}`: Get automation
- `PUT /api/v1/automations/{automation_id}`: Update automation (increments version)
- `POST /api/v1/automations/{automation_id}/enable`: Enable automation
- `POST /api/v1/automations/{automation_id}/disable`: Disable automation
- `POST /api/v1/automations/{automation_id}/trigger`: Trigger automation
- `POST /api/v1/automations/{automation_id}/dry-run`: Dry-run automation plan
- `GET /api/v1/automations/{automation_id}/executions`: List automation executions
- `GET /api/v1/automations/{automation_id}/status`: Get automation status

---

## Deterministic Development Mode

`DeterministicSchedulerBackend` allows full control over simulated clock time (`advance_time`, `set_time`) and manual tick executions (`run_due`, `emit_event`), enabling fast, deterministic unit and integration testing.
