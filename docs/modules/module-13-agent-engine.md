# Module 13 — Agent Engine

## 1. Purpose
The Agent Engine acts as the coordination and orchestration layer of the Max Personal AI Runtime. It represents logical agents, roles, capabilities, limits, assignments, runs, execution state transitions, operational event traces, and sub-task delegations.

It bridges Module 11 (Reasoning & Planning), Module 12 (Task Engine), Module 04 (AI Runtime), and Module 06 (Context Management), while strictly enforcing boundaries against Tool execution (Module 14) and Permission checking (Module 15).

## 2. Architecture
```
User -> Conversation -> Context -> Reasoning -> Plan -> Tasks -> AGENT ENGINE -> Future Tools -> Future Permissions -> Future Execution
```

The Agent Engine answers:
- Which agent should coordinate this task?
- What work is assigned to it?
- What is its current lifecycle and run state?
- What happened during the execution run?
- What result, failure, or boundary request intent did it produce?

It does NOT execute tools or grant permissions.

## 3. Domain Model
- `Agent`: Core entity representing logical AI worker/coordinator.
- `AgentType`: `GENERAL`, `SPECIALIST`, `COORDINATOR`, `REVIEWER`, `PLANNER`, `EXECUTOR`.
- `AgentRole`: `ASSISTANT`, `COORDINATOR`, `RESEARCHER`, `PLANNER`, `CODER`, `REVIEWER`, `ANALYST`, `SYSTEM`.
- `AgentStatus`: `CREATED`, `ACTIVE`, `PAUSED`, `DISABLED`, `ARCHIVED`.
- `AgentCapability`: Theoretical capabilities (`PLANNING`, `TASK_COORDINATION`, `RESEARCH`, `ANALYSIS`, `CODE_REVIEW`, `CONTENT_GENERATION`, `DELEGATION`, `RESULT_REVIEW`).
- `AgentConfiguration`: Model settings (`model_id`, `temperature`, `max_output_tokens`, `retry_policy`).
- `AgentLimits`: Operational safety limits (`max_tasks_per_run`, `max_steps_per_run`, `max_delegations`, `max_retries`, `max_context_items`, `max_run_duration`, `max_agent_depth`).
- `AgentAssignment`: Logical link connecting `Agent` -> `Task` (`ASSIGNED`, `ACCEPTED`, `REJECTED`, `STARTED`, `COMPLETED`, `FAILED`, `CANCELLED`).
- `AgentRun`: Execution lifecycle instance (`CREATED`, `INITIALIZING`, `READY`, `RUNNING`, `WAITING`, `PAUSED`, `COMPLETED`, `FAILED`, `CANCELLED`, `TIMED_OUT`).
- `AgentExecutionMode`: `SYNCHRONOUS`, `ASYNCHRONOUS`, `SUPERVISED`, `DRY_RUN`.
- `AgentResult`: Structured outcome info without private chain-of-thought.
- `AgentFailure`: Normalized failure category, error code, message, and retryability.
- `AgentRetryPolicy`: Deterministic retry strategy (`NONE`, `FIXED`, `EXPONENTIAL`).
- `AgentTrace` & `AgentEvent`: Immutable operational timeline events.
- `AgentDelegation`: Parent-child delegation tracking with recursion limits and cycle detection.

## 4. Agent Lifecycle
Strict state machine transitions:
- `CREATED` -> `ACTIVE` | `DISABLED`
- `ACTIVE` -> `PAUSED` | `DISABLED` | `ARCHIVED`
- `PAUSED` -> `ACTIVE` | `DISABLED`
- `DISABLED` -> `ACTIVE` | `ARCHIVED`
- `ARCHIVED` (Terminal)

## 5. Agent Run Lifecycle
State transitions:
- `CREATED` -> `INITIALIZING`
- `INITIALIZING` -> `READY` | `FAILED` | `CANCELLED`
- `READY` -> `RUNNING` | `CANCELLED`
- `RUNNING` -> `WAITING` | `PAUSED` | `COMPLETED` | `FAILED` | `CANCELLED` | `TIMED_OUT`
- `WAITING` -> `RUNNING` | `CANCELLED` | `TIMED_OUT`
- `PAUSED` -> `RUNNING` | `CANCELLED`

## 6. Assignment Lifecycle
- `ASSIGNED` -> `ACCEPTED` | `REJECTED` | `CANCELLED`
- `ACCEPTED` -> `STARTED` | `CANCELLED`
- `STARTED` -> `COMPLETED` | `FAILED` | `CANCELLED`

## 7. Delegation
Allows parent agents to delegate sub-tasks to child agents with:
- `max_delegation_depth` limit check
- `max_delegations` per run limit check
- Graph cycle detection (`Agent A -> Agent B -> Agent A` rejected with `DelegationCycleError`)

## 8. Capability Model
Claims what an agent can theoretically handle (`AgentCapability`). Distinguishes capability claims from execution permissions.

## 9. Agent Selection
`CapabilityMatcher` and `AgentSelectionService` deterministically select active agents matching required capabilities, workload capacity, and role/type preferences.

## 10. Agent Coordinator
`AgentCoordinator` receives an `AgentCoordinationRequest`, resolves assignment and context, executes logic via `DevelopmentAgent` or provider-neutral `AIRuntime`, interprets the decision, and produces a `AgentNextAction` intent.

## 11. Runtime Integration
Integrates with Module 04 provider-neutral `AIRuntime` and Module 05 model specifications without hardcoding model providers.

## 12. Context Integration
Uses Module 06 `ContextManager` to bundle system, identity, conversation, memory, knowledge, RAG, plan, and task context.

## 13. Tool Boundary
Exposes `ToolExecutionGateway` and `ToolRequestIntent`. When `NextAction` requests a tool, intent is created with `status="NOT_IMPLEMENTED"`. **Zero tool execution occurs.**

## 14. Permission Boundary
Exposes `PermissionCheckPort` and `PermissionRequestIntent`. When `NextAction` requests permission, intent is created with `status="NOT_IMPLEMENTED"`. **Zero automatic permission granting occurs.**

## 15. API Reference
REST API under `/api/v1/agents`:
- `POST /api/v1/agents`
- `GET /api/v1/agents`
- `GET /api/v1/agents/{agent_id}`
- `PATCH /api/v1/agents/{agent_id}`
- `DELETE /api/v1/agents/{agent_id}`
- `POST /api/v1/agents/{agent_id}/activate`
- `POST /api/v1/agents/{agent_id}/pause`
- `POST /api/v1/agents/{agent_id}/disable`
- `POST /api/v1/agents/{agent_id}/archive`
- `GET /api/v1/agents/{agent_id}/capabilities`
- `GET /api/v1/agents/{agent_id}/availability`
- `POST /api/v1/agents/{agent_id}/assignments`
- `GET /api/v1/agents/{agent_id}/assignments`
- `POST /api/v1/agents/{agent_id}/runs`
- `GET /api/v1/agents/{agent_id}/runs`
- `GET /api/v1/agents/{agent_id}/runs/{run_id}`
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/start`
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/pause`
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/resume`
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/cancel`
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/retry`
- `GET /api/v1/agents/{agent_id}/runs/{run_id}/trace`
- `POST /api/v1/agents/{agent_id}/delegations`
- `GET /api/v1/agents/{agent_id}/delegations`
- `POST /api/v1/agents/select`

## 16. Error Model
Domain exceptions extending `AgentError`:
- `AgentNotFoundError`
- `AgentInactiveError`
- `AgentCapabilityMismatchError`
- `AgentAssignmentNotFoundError`
- `AgentRunNotFoundError`
- `InvalidAgentStateTransitionError`
- `InvalidRunStateTransitionError`
- `AgentLimitExceededError`
- `DelegationCycleError`
- `DelegationLimitExceededError`
- `AgentUnavailableError`
- `AgentExecutionBoundaryError`

## 17. Configuration
Configuration parameters in `AgentSettings`:
- `MAX_AGENT_ENABLED` (default: True)
- `MAX_AGENT_MAX_CONCURRENT_RUNS` (default: 10)
- `MAX_AGENT_DEFAULT_MAX_RETRIES` (default: 3)
- `MAX_AGENT_MAX_DELEGATION_DEPTH` (default: 5)
- `MAX_AGENT_MAX_DELEGATIONS` (default: 20)
- `MAX_AGENT_DEFAULT_EXECUTION_MODE` (default: "DRY_RUN")

## 18. Security
Capabilities are not permissions. No shell execution, arbitrary file access, network requests, or system actions are permitted in Module 13.

## 19. Privacy
Respects user ownership across all domain objects (`owner_id`). No private chain-of-thought or sensitive context is stored in traces.

## 20. Testing
Comprehensive test suite including unit domain tests, service tests, coordinator tests, delegation cycle tests, boundary tests, API tests, and E2E scenario tests using `DevelopmentAgent`.

## 21. Future Extensions
- Module 14: Tool Registry & Tool Execution
- Module 15: Permission & Security Engine
