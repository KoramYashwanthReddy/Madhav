# Module 12 — Task Engine Architecture Specification

## System Architecture

```
User / API
   ↓
API Routes (/api/v1/tasks, /api/v1/task-groups, /api/v1/plans/{id}/tasks)
   ↓
TaskService
   ├── TaskStateMachine (State Transitions & Validations)
   ├── TaskValidator (DFS Cycle Checks & Nesting Depth)
   └── PlanTaskMapper (Module 11 Plan → Task Conversion)
   ↓
Repositories (Task, Dependency, Group, History)
```

## Architectural Isolation Guarantees

1. **Passive Task Data Model**: Tasks represent intended work state and metadata. They **NEVER** execute system commands, filesystem edits, or external network requests.
2. **Deterministic State Machine**: Every state transition is explicitly validated.
3. **Idempotent Plan Mapping**: Converting a Module 11 plan twice generates zero duplicate tasks.
4. **Privacy-Safe Logging**: Logging writes only safe metadata (`task_id`, `status`, `progress`, `duration_ms`). Sensitive user payload text is never logged.
