# Module 11 — Reasoning & Planning Engine

## Overview

The Reasoning & Planning Engine provides Max with structured goal understanding, constraint analysis, dependency tracking, plan synthesis, plan validation, version control, and revision capability. 

> [!IMPORTANT]
> **NON-NEGOTIABLE ARCHITECTURAL RULE:**
> Module 11 **thinks and plans only**. It **NEVER executes** actions. Plan steps represent structured data intended for future execution engines (Module 12 Task Engine / Module 13 Agent Engine). Module 11 strictly performs zero terminal commands, zero file mutations, zero network requests, zero browser actions, and zero tool invocations.

---

## Key Domain Concepts

### 1. Reasoning Domain Model
- **`ReasoningRequest`**: An explicit request containing an objective, context selections, constraints, reasoning mode, and plan depth.
- **`ReasoningObjective`**: Title, description, desired outcome, success criteria, priority, and optional explicit deadline.
- **`ReasoningContext`**: Consolidated information assembled via Module 06 `ContextManager`, containing conversation, memory, personal knowledge, retrieval, and custom system inputs.
- **`ReasoningObservation`**: Information items extracted with provenance references (`MEMORY`, `KNOWLEDGE`, `RAG`, `CONVERSATION`).
- **`ReasoningAssumption`**: Explicit hypotheses with confidence ratings and status (`UNVERIFIED`, `VERIFIED`, `DISPROVED`).
- **`ReasoningConstraint`**: Hard (`HARD`) vs Soft (`SOFT`) constraints across domains (budget, tech, time, environment, preference).
- **`MissingInformation`**: Identified gaps in current context, classified as blocking or non-blocking.
- **`ReasoningConclusion`**: Structured deductions and key findings supporting the synthesized plan.
- **`ReasoningResult`**: Complete, machine-readable summary containing objective analysis, observations, assumptions, constraints, missing info, conclusions, risk analysis, confidence rating, and synthesized plan.

### 2. Planning Domain Model
- **`Plan`**: Structured graph of steps representing a sequence of intended actions.
- **`PlanStep`**: Unit step with `id`, `sequence`, `title`, `description`, `objective`, `prerequisites`, `dependencies`, `expected_output`, `estimated_complexity`, `risk_level`, and `status`.
- **`PlanDependency`**: Explicit dependency link specifying that step $B$ requires step $A$.
- **`PlanConstraint`**: Explicit hard or soft rule governing step ordering or execution context.
- **`PlanRisk`**: Risk item specifying severity (`LOW`, `MEDIUM`, `HIGH`), likelihood, affected step, and mitigation strategy.
- **`PlanValidationResult`**: Deterministic status (`VALID`, `INVALID`, `CIRCULAR_DEPENDENCY`, `HARD_CONSTRAINT_VIOLATED`, `MISSING_PREREQUISITE`), completeness evaluation (`COMPLETE`, `PARTIAL`, `BLOCKED`, `INVALID`, `UNKNOWN`), and explicit error messages.
- **`PlanVersion`**: Immutable snapshot of plan state supporting full audit trail and parent version links.
- **`PlanDiff`**: Version comparison showing added steps, removed steps, updated steps, dependency changes, constraint changes, and risk changes.

---

## Privacy Guardrail (No Chain-of-Thought Persistence)

To maintain user privacy and system security:
- **Private internal chain-of-thought text is NEVER persisted or exposed.**
- The engine stores only structured metadata, explicit assumptions, hard constraints, conclusions, risk summaries, plan steps, and user-facing explanations.

---

## Cycle Detection & Plan Validation

`PlanValidator` performs deterministic graph validation using Depth-First Search (DFS):
- Detects circular dependencies (e.g. $A \rightarrow B \rightarrow C \rightarrow A$) and raises `CircularDependencyError`.
- Validates missing prerequisite references and dangling step dependencies.
- Enforces hard constraint satisfaction.
- Evaluates plan completeness without arbitrary numeric quality scores.

---

## Service Layer & API Endpoints

### Reasoning Endpoints
- `POST /api/v1/reasoning`: Submit a reasoning request.
- `GET /api/v1/reasoning/{reasoning_id}`: Retrieve structured reasoning result.
- `POST /api/v1/reasoning/{reasoning_id}/validate`: Validate synthesized plan.
- `POST /api/v1/reasoning/{reasoning_id}/revise`: Revise plan based on new context or constraints.
- `GET /api/v1/reasoning/{reasoning_id}/summary`: Retrieve user-facing summary & explanation.

### Plan Endpoints
- `POST /api/v1/plans`: Create a standalone plan.
- `GET /api/v1/plans`: List plans owned by user.
- `GET /api/v1/plans/{plan_id}`: Retrieve plan.
- `GET /api/v1/plans/{plan_id}/versions`: Get all version snapshots.
- `POST /api/v1/plans/{plan_id}/revise`: Revise a plan into a new version.
- `POST /api/v1/plans/{plan_id}/validate`: Validate a plan graph.
- `GET /api/v1/plans/{plan_id}/summary`: Retrieve concise plan summary.

---

## Testing & Offline Guarantee

The system includes a `DevelopmentReasoningProvider` which generates deterministic plans and reasoning results without calling external APIs or requiring credentials. Full unit, integration, and end-to-end tests verify 100% offline functionality.
