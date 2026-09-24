"""Domain models for Module 22 — Coding Agent."""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from max.coding.domain.enums import (
    ChangeType,
    CodingMode,
    CodingStatus,
    FailureCategory,
    IssueCategory,
    IssueSeverity,
    ProjectType,
    SymbolType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CodingObjective(BaseModel):
    """Core software engineering goal and scope description."""

    summary: str = Field(description="High-level description of coding task")
    details: str | None = Field(default=None, description="Detailed requirements or user prompt")
    target_files: list[str] = Field(default_factory=list, description="Target files or file glob patterns")


class CodingScope(BaseModel):
    """Scope boundaries and security restrictions for coding tasks."""

    allowed_directories: list[str] = Field(
        default_factory=list, description="Allowed directory roots (relative to repo)"
    )
    blocked_directories: list[str] = Field(
        default_factory=lambda: [".git", ".env", "node_modules", ".venv", "__pycache__"],
        description="Explicitly blocked directory roots",
    )
    allowed_file_extensions: list[str] = Field(
        default_factory=list, description="Allowed file extensions (empty = all except protected)"
    )
    protected_patterns: list[str] = Field(
        default_factory=lambda: [".env*", "*.pem", "*.key", "id_rsa*", "*.secret"],
        description="Glob patterns for protected sensitive files",
    )


class CodingRequest(BaseModel):
    """Request payload initiating a Coding Session or Task."""

    id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    owner_id: str = Field(default="user_default", description="Requesting user or agent ID")
    repo_path: str = Field(description="Absolute path to target repository root")
    objective: CodingObjective = Field(description="Coding task goal")
    mode: CodingMode = Field(default=CodingMode.FEATURE_IMPLEMENTATION, description="Coding mode")
    scope: CodingScope = Field(default_factory=CodingScope, description="Security scope boundaries")
    created_at: datetime = Field(default_factory=_utc_now)


class ProjectMetadata(BaseModel):
    """Metadata extracted during repository analysis."""

    project_name: str = Field(default="Unknown Project")
    repo_root: str = Field(description="Absolute repository root path")
    project_type: ProjectType = Field(default=ProjectType.UNKNOWN)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    build_system: str | None = Field(default=None)
    package_manager: str | None = Field(default=None)
    test_framework: str | None = Field(default=None)
    lint_tools: list[str] = Field(default_factory=list)
    type_checker: str | None = Field(default=None)
    entry_points: list[str] = Field(default_factory=list)
    source_directories: list[str] = Field(default_factory=list)
    test_directories: list[str] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)


class RepositoryContext(BaseModel):
    """Context representation of an analyzed repository."""

    repo_root: str
    metadata: ProjectMetadata
    total_files_count: int = Field(default=0)
    file_tree: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=_utc_now)


class CodeSymbol(BaseModel):
    """Parsed code symbol definition."""

    name: str
    symbol_type: SymbolType
    file_path: str = Field(description="Relative path inside repo")
    line_number: int = Field(default=1)
    end_line_number: int | None = Field(default=None)
    docstring: str | None = Field(default=None)
    signature: str | None = Field(default=None)


class DependencyGraph(BaseModel):
    """Graph mapping relationships between source files and packages."""

    nodes: list[str] = Field(default_factory=list, description="List of file paths")
    edges: list[dict[str, str]] = Field(
        default_factory=list, description="List of dicts {'source': file, 'target': file}"
    )


class CodeIssue(BaseModel):
    """Static analysis or security defect item."""

    id: str = Field(default_factory=lambda: f"iss_{uuid.uuid4().hex[:8]}")
    file_path: str
    line_number: int = Field(default=1)
    severity: IssueSeverity = Field(default=IssueSeverity.LOW)
    category: IssueCategory = Field(default=IssueCategory.BUG_RISK)
    message: str
    rule_id: str | None = Field(default=None)


class CodeAnalysis(BaseModel):
    """Static analysis output summary."""

    repo_root: str
    issues: list[CodeIssue] = Field(default_factory=list)
    symbols: list[CodeSymbol] = Field(default_factory=list)
    dependency_graph: DependencyGraph = Field(default_factory=DependencyGraph)
    analyzed_at: datetime = Field(default_factory=_utc_now)


class CodePlanStep(BaseModel):
    """Individual step within a structured CodePlan."""

    step_number: int = Field(description="1-indexed step sequence")
    action_type: str = Field(description="Type of action (e.g. READ, EDIT, CREATE, DELETE, TEST, BUILD)")
    description: str = Field(description="Step description")
    target_files: list[str] = Field(default_factory=list)
    completed: bool = Field(default=False)


class CodePlan(BaseModel):
    """Structured implementation plan generated prior to code edits."""

    session_id: str
    objective: str
    steps: list[CodePlanStep] = Field(default_factory=list)
    affected_files: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)


class PatchHunk(BaseModel):
    """Single hunk within a patch diff."""

    start_line: int
    end_line: int
    old_content: str
    new_content: str


class Patch(BaseModel):
    """Targeted file patch specification."""

    id: str = Field(default_factory=lambda: f"pat_{uuid.uuid4().hex[:10]}")
    change_type: ChangeType = Field(default=ChangeType.MODIFY_FILE)
    file_path: str = Field(description="Relative path inside repo")
    hunks: list[PatchHunk] = Field(default_factory=list)
    original_content_hash: str = Field(default="", description="Hash of file prior to edit")
    new_content: str | None = Field(default=None, description="Full file content if creating new file")
    reason: str = Field(default="Code modification")


class ChangeSet(BaseModel):
    """Group of patches forming a single atomic modification unit."""

    id: str = Field(default_factory=lambda: f"cs_{uuid.uuid4().hex[:10]}")
    session_id: str
    patches: list[Patch] = Field(default_factory=list)
    is_applied: bool = Field(default=False)
    applied_at: datetime | None = Field(default=None)
    backup_data: dict[str, str] = Field(
        default_factory=dict, description="Map of file_path -> pre-patch original content for rollback"
    )


class TestRun(BaseModel):
    """Execution result of unit or integration tests."""

    id: str = Field(default_factory=lambda: f"tst_{uuid.uuid4().hex[:8]}")
    command: str
    exit_code: int = Field(default=0)
    passed_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    output: str = Field(default="")
    duration_seconds: float = Field(default=0.0)
    executed_at: datetime = Field(default_factory=_utc_now)


class BuildRun(BaseModel):
    """Execution result of a project compilation or build command."""

    id: str = Field(default_factory=lambda: f"bld_{uuid.uuid4().hex[:8]}")
    command: str
    exit_code: int = Field(default=0)
    success: bool = Field(default=True)
    output: str = Field(default="")
    duration_seconds: float = Field(default=0.0)
    executed_at: datetime = Field(default_factory=_utc_now)


class LintRun(BaseModel):
    """Execution result of code linter."""

    id: str = Field(default_factory=lambda: f"lnt_{uuid.uuid4().hex[:8]}")
    command: str
    exit_code: int = Field(default=0)
    issues_found: int = Field(default=0)
    output: str = Field(default="")
    executed_at: datetime = Field(default_factory=_utc_now)


class TypeCheckRun(BaseModel):
    """Execution result of static type checker."""

    id: str = Field(default_factory=lambda: f"typ_{uuid.uuid4().hex[:8]}")
    command: str
    exit_code: int = Field(default=0)
    errors_found: int = Field(default=0)
    output: str = Field(default="")
    executed_at: datetime = Field(default_factory=_utc_now)


class DebugFinding(BaseModel):
    """Structured diagnostic finding from failure analysis."""

    failure_category: FailureCategory = Field(default=FailureCategory.UNKNOWN)
    suspected_file: str | None = Field(default=None)
    suspected_line: int | None = Field(default=None)
    error_message: str = Field(default="")
    suggested_fix: str = Field(default="")


class DebugSession(BaseModel):
    """Debugging session record tracking fix iterations."""

    session_id: str
    attempt_count: int = Field(default=1)
    max_attempts: int = Field(default=3)
    findings: list[DebugFinding] = Field(default_factory=list)
    resolved: bool = Field(default=False)


class CodeReviewFinding(BaseModel):
    """Finding item from code review or security review."""

    file_path: str
    line_number: int = Field(default=1)
    severity: IssueSeverity = Field(default=IssueSeverity.LOW)
    title: str
    description: str
    recommendation: str


class CodeReview(BaseModel):
    """Structured code review output."""

    session_id: str
    summary: str
    findings: list[CodeReviewFinding] = Field(default_factory=list)
    overall_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    reviewed_at: datetime = Field(default_factory=_utc_now)


class CodingSession(BaseModel):
    """Complete Coding Agent execution session state."""

    id: str = Field(default_factory=lambda: f"cses_{uuid.uuid4().hex[:12]}")
    request: CodingRequest
    status: CodingStatus = Field(default=CodingStatus.CREATED)
    context: RepositoryContext | None = Field(default=None)
    plan: CodePlan | None = Field(default=None)
    active_changeset: ChangeSet | None = Field(default=None)
    test_runs: list[TestRun] = Field(default_factory=list)
    build_runs: list[BuildRun] = Field(default_factory=list)
    lint_runs: list[LintRun] = Field(default_factory=list)
    typecheck_runs: list[TypeCheckRun] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class CodingResult(BaseModel):
    """Final output object returned by Coding Agent."""

    session_id: str
    status: CodingStatus
    summary: str
    affected_files: list[str] = Field(default_factory=list)
    applied_changeset_id: str | None = Field(default=None)
    test_summary: str | None = Field(default=None)
    review: CodeReview | None = Field(default=None)
    completed_at: datetime = Field(default_factory=_utc_now)


class CodingAuditEvent(BaseModel):
    """Audit log entry for coding actions."""

    id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:10]}")
    timestamp: datetime = Field(default_factory=_utc_now)
    session_id: str
    event_type: str
    owner_id: str = Field(default="system")
    details: dict[str, Any] = Field(default_factory=dict)
