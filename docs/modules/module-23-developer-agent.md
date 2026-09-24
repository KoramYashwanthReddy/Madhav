# Module 23 — Developer Agent

## Purpose
Module 23 provides Max with secure, structured GitHub and developer workflow orchestration capabilities. It enables Max to manage Git repositories, branches, commits, pull requests, issues, and multi-step developer lifecycles (Feature, Bugfix, Hotfix, Release, Refactor) while strictly delegating code modifications to Module 22 (Coding Agent), shell/Git execution to Module 18 (Terminal Agent), and high-risk operations to Module 15 (Permission Gate).

## Architecture

```
User / API Request
        ↓
Developer Agent (Module 23)
        ↓
┌───────────────────┬───────────────────┬───────────────────┐
│   RepoService     │   IssueService    │    PRService      │
└─────────┬─────────┴─────────┬─────────┴─────────┬─────────┘
          │                   │                   │
          ▼                   ▼                   ▼
   DeveloperSession     DeveloperIssue       PullRequest
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                     WorkflowService (State Machine)
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
     GitOperationPolicy                 Module 22 (Coding Agent)
             │                                 │
             ▼                                 ▼
   Module 15 (Permission Gate)        Local Code Changes
             │
             ▼
   Module 18 (Terminal Agent)
             │
             ▼
       Git Repository
```

## Domain Models & Lifecycles

### Session & Workflow States
- **DevSessionStatus**: `OPEN`, `CLOSED`, `ERROR`
- **WorkflowType**: `FEATURE`, `BUGFIX`, `HOTFIX`, `RELEASE`, `REFACTOR`, `CUSTOM`
- **WorkflowStep**: `INIT`, `CREATE_BRANCH`, `DELEGATE_CODING`, `STAGE_AND_COMMIT`, `PUSH`, `OPEN_PR`, `AWAIT_REVIEW`, `MERGE`, `TAG_RELEASE`, `CLEANUP`, `COMPLETED`, `FAILED`
- **PRStatus**: `DRAFT`, `OPEN`, `APPROVED`, `CHANGES_REQUESTED`, `MERGED`, `CLOSED`
- **IssueStatus**: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`
- **CIRunStatus**: `QUEUED`, `IN_PROGRESS`, `SUCCESS`, `FAILED`, `CANCELLED`
- **MergeStrategy**: `MERGE_COMMIT`, `SQUASH`, `REBASE`
- **GitOperationRisk**: `READ_ONLY`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

## Core Subsystems

1. **GitService**: Wraps all Git operations through Module 18 `CommandRequest` (no raw subprocess calls). Evaluates operation risk with `GitOperationPolicy` and enforces `PermissionGate` approval for HIGH/CRITICAL actions.
2. **RepoService**: Manages `DeveloperSession` lifecycles and repository introspection (`validate_repo`, `get_status`, `list_branches`).
3. **IssueService**: In-memory CRUD lifecycle for `DeveloperIssue` tracking linked to developer sessions.
4. **PRService**: Manages `PullRequest` lifecycles, review status, and branch merges (protected branch merges trigger `PermissionGate`).
5. **WorkflowService**: Deterministic state machine orchestrating multi-step workflows. Coding work is delegated exclusively to Module 22 by recording `coding_session_id`.
6. **DeveloperService**: Unified service facade exposing clean high-level operations for API routes.
7. **DeveloperContainer**: Dependency injection container providing singleton instances and test isolation reset capabilities.

## Security Model & Policy Matrix

| Operation | Risk Level | Requires PermissionGate Approval |
|---|---|---|
| `git status`, `git log`, `git diff` | `READ_ONLY` | No |
| `git checkout`, `create branch` | `LOW` | No |
| `git commit`, `git push` | `MEDIUM` | No (standard dev branch) |
| `git push --force` | `HIGH` | **Yes — explicit approval required** |
| `git merge` to protected branch | `HIGH` | **Yes — explicit approval required** |
| `git reset --hard` | `HIGH` | **Yes — explicit approval required** |
| Delete protected branch (`git branch -D main`) | `CRITICAL` | **Yes — explicit approval required** |

## API Endpoints (`/api/v1/developer`)

- `GET /api/v1/developer/health`: Subsystem health check.
- `POST /api/v1/developer/sessions`: Open developer session for target repository.
- `GET /api/v1/developer/sessions`: List active developer sessions.
- `GET /api/v1/developer/sessions/{session_id}`: Retrieve session details.
- `DELETE /api/v1/developer/sessions/{session_id}`: Close session.
- `GET /api/v1/developer/sessions/{session_id}/status`: Get repository Git status.
- `POST /api/v1/developer/sessions/{session_id}/branches`: Create branch.
- `POST /api/v1/developer/sessions/{session_id}/branches/{branch}/checkout`: Checkout branch.
- `GET /api/v1/developer/sessions/{session_id}/log`: Retrieve Git log.
- `POST /api/v1/developer/sessions/{session_id}/commit`: Stage and commit changes.
- `POST /api/v1/developer/sessions/{session_id}/push`: Push commits to remote.
- `POST /api/v1/developer/sessions/{session_id}/pull`: Pull commits from remote.
- `POST /api/v1/developer/sessions/{session_id}/workflows`: Start workflow.
- `GET /api/v1/developer/sessions/{session_id}/workflows/{workflow_id}`: Get workflow status.
- `POST /api/v1/developer/sessions/{session_id}/workflows/{workflow_id}/advance`: Advance workflow step.
- `GET /api/v1/developer/sessions/{session_id}/issues`: List session issues.
- `POST /api/v1/developer/sessions/{session_id}/issues`: Create issue.
- `GET /api/v1/developer/sessions/{session_id}/prs`: List session PRs.
- `POST /api/v1/developer/sessions/{session_id}/prs`: Create pull request.
- `POST /api/v1/developer/sessions/{session_id}/prs/{pr_id}/merge`: Merge pull request.
