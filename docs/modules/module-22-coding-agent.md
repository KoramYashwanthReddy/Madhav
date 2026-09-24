# Module 22 — Coding Agent

## Purpose
Module 22 provides Max with production-quality Software Engineering Intelligence and controlled coding workflows. It allows Max to safely analyze, understand, plan, modify, test, lint, typecheck, build, debug, review, and refactor software projects while maintaining strict integration with Module 15 (Permission Gate), Module 17 (Filesystem Agent), Module 18 (Terminal Agent), and Module 14 (Tool Registry).

## Architecture

```
User / Agent
      ↓
Coding Request
      ↓
Coding Agent (Module 22)
      ↓
Repository Analysis (Module 17)
      ↓
Code Analysis & Search
      ↓
Create Coding Plan
      ↓
Generate Proposed Changes (Patches)
      ↓
Permission Engine (Module 15)
      ↓
Apply Changes (Module 17)
      ↓
Run Validation (Module 18)
      ↓
Analyze Results & Debug
      ↓
Verify & Audit (Module 01)
      ↓
Produce Coding Result
```

## Domain Models & Lifecycles

### Coding Lifecycle States
- `CREATED`: Session initiated.
- `ANALYZING`: Scanning repository structure and detecting project metadata.
- `PLANNING`: Formulating structured `CodePlan` steps.
- `WAITING_FOR_APPROVAL`: Waiting for user approval on plan/patches (for medium/high risk changes).
- `MODIFYING`: Applying patches to files via Module 17.
- `VALIDATING`: Running formatting and syntax checks.
- `TESTING`: Executing test suite via Module 18.
- `DEBUGGING`: Analyzing test/build failures, classifying errors, and iterating on fixes.
- `REVIEWING`: Generating quality reviews, security reviews, and explanations.
- `COMPLETED`: Session successfully completed all objectives.
- `FAILED`: Session failed or exceeded maximum fix attempts.
- `CANCELLED`: Session manually cancelled.

### Coding Modes
- `CODE_EXPLANATION`, `CODE_ANALYSIS`, `BUG_FIX`, `FEATURE_IMPLEMENTATION`, `REFACTOR`, `TEST_GENERATION`, `TEST_REPAIR`, `PERFORMANCE_ANALYSIS`, `SECURITY_REVIEW`, `CODE_REVIEW`, `DOCUMENTATION`, `DEPENDENCY_ANALYSIS`, `BUILD_DEBUGGING`.

## Core Subsystems

1. **RepositoryAnalyzer**: Detects project types (Python, Java, JS, TS, Rust, Go, C/C++, C#, Kotlin, PHP) and extracts build tools, dependency manifests, test frameworks, and entry points.
2. **CodeSearchService**: Safe, bounded reading of files, extract top-level class/function symbols, and query text matches using `FilesystemService.execute_operation`.
3. **CodePlanner**: Generates structured, step-by-step `CodePlan` with targets, dependencies, risks, and validation criteria.
4. **PatchService**: Patch-first modification architecture. Supports diff preview generation (`a/` to `b/`), stale-patch detection using SHA-256 content hashes, changeset application via `FilesystemService`, and full atomic rollback restoring pre-patch file states.
5. **ValidationPipeline**: Invokes build, test, lint, and typecheck commands safely via `TerminalService.execute_command` with structured `CommandRequest` instances.
6. **DebuggerService**: Failure categorization (`CODE_ERROR`, `TEST_FAILURE`, `BUILD_ERROR`, etc.) and bounded fix iteration loop (max 3 attempts).
7. **CodeReviewer**: High-level code explanation, architecture review, and defensive security review.
8. **CodeSecurityEnforcer & Audit**: Protected path security (`.env`, `.git`, SSH/private keys), prompt injection defense treating repository content as untrusted data, and redacted audit logging.

## Security Guarantees
- **Strict Module Boundaries**: Never uses raw `open()`, `os.remove()`, or `subprocess.run()` directly for privileged actions; all file/terminal operations route through Module 17 and Module 18.
- **Permission Gate**: All code modifications and terminal executions consult Module 15 `PermissionGate`.
- **Git & Developer Agent Boundary**: Module 22 handles local code analysis and patches only. Git remote push, pull requests, and GitHub management are strictly delegated to Module 23.
- **Untrusted Code Injection Protection**: Comments, README files, and package manifests containing instructions like "ignore previous instructions" or "curl malicious site" are treated strictly as `UNTRUSTED_DATA` and never executed.

## API Endpoints (`/api/v1/coding`)
- `POST /api/v1/coding/sessions`: Create new coding session.
- `GET /api/v1/coding/sessions/{session_id}`: Retrieve session status.
- `POST /api/v1/coding/sessions/{session_id}/analyze`: Analyze repository root.
- `POST /api/v1/coding/sessions/{session_id}/search`: Search files or symbols.
- `POST /api/v1/coding/sessions/{session_id}/plan`: Generate implementation plan.
- `POST /api/v1/coding/sessions/{session_id}/changes/preview`: Generate diff preview.
- `POST /api/v1/coding/sessions/{session_id}/changes/apply`: Apply changeset patches.
- `POST /api/v1/coding/sessions/{session_id}/validate`: Execute test/build validation pipeline.
- `POST /api/v1/coding/sessions/{session_id}/debug`: Analyze failures and propose fix.
- `POST /api/v1/coding/sessions/{session_id}/review`: Perform code quality & security review.
- `POST /api/v1/coding/sessions/{session_id}/rollback`: Rollback applied changeset.
