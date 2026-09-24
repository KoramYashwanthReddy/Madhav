"""Domain models for Module 18 — Terminal Agent.

These models represent the full lifecycle of a terminal command: request,
execution record, result, audit trace, and session metadata.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.terminal.domain.enums import (
    CommandCategory,
    CommandFailureReason,
    CommandRiskLevel,
    CommandStatus,
    SessionStatus,
    TerminalShell,
)

# ---------------------------------------------------------------------------
# Command Request / Response
# ---------------------------------------------------------------------------


class CommandRequest(BaseModel):
    """A structured, validated request to execute a terminal command."""

    request_id: str = Field(
        default_factory=lambda: f"cmd_{uuid.uuid4().hex[:12]}",
        description="Unique command request identifier",
    )
    command: str = Field(..., description="Executable name (no shell expansion)")
    args: list[str] = Field(default_factory=list, description="Explicit argument list")
    shell: TerminalShell = Field(
        default=TerminalShell.POWERSHELL, description="Target shell backend"
    )
    working_directory: str | None = Field(
        default=None, description="Working directory for command execution"
    )
    environment: dict[str, str] = Field(
        default_factory=dict, description="Additional safe environment variables"
    )
    timeout: float = Field(
        default=30.0, ge=0.1, le=300.0, description="Execution timeout in seconds"
    )
    stdin_data: str | None = Field(
        default=None, description="Optional stdin data (strictly controlled)"
    )
    owner_id: str = Field(default="system", description="Owner identifier for audit")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    dry_run: bool = Field(default=False, description="Simulate without execution")


class CommandResult(BaseModel):
    """Structured result returned after command execution."""

    request_id: str = Field(..., description="Associated command request ID")
    status: CommandStatus = Field(..., description="Final execution status")
    shell: TerminalShell = Field(..., description="Shell used for execution")
    command: str = Field(..., description="Executed command")
    args: list[str] = Field(default_factory=list, description="Argument list")
    exit_code: int | None = Field(default=None, description="Process exit code (None if not run)")
    stdout: str = Field(default="", description="Captured standard output (sanitized)")
    stderr: str = Field(default="", description="Captured standard error (sanitized)")
    duration: float = Field(default=0.0, ge=0.0, description="Execution duration in seconds")
    working_directory: str | None = Field(
        default=None, description="Working directory used"
    )
    timed_out: bool = Field(default=False, description="Whether execution was terminated by timeout")
    failure_reason: CommandFailureReason | None = Field(
        default=None, description="Structured failure reason if status is FAILED or REJECTED"
    )
    failure_message: str | None = Field(
        default=None, description="Human-readable failure description"
    )
    simulated: bool = Field(default=False, description="Whether this was a dry-run simulation")
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Execution start timestamp"
    )
    completed_at: datetime | None = Field(
        default=None, description="Execution completion timestamp"
    )


# ---------------------------------------------------------------------------
# Command Policy & Classification
# ---------------------------------------------------------------------------


class CommandClassification(BaseModel):
    """Risk classification and policy verdict for a command."""

    command: str = Field(..., description="Command being classified")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    category: CommandCategory = Field(..., description="Semantic category")
    risk_level: CommandRiskLevel = Field(..., description="Evaluated risk level")
    is_allowed: bool = Field(..., description="Whether command is allowed by policy")
    rejection_reason: str | None = Field(
        default=None, description="Reason for policy rejection if not allowed"
    )
    requires_elevated_permission: bool = Field(
        default=False, description="Whether CRITICAL risk permission is required"
    )
    notes: list[str] = Field(
        default_factory=list, description="Policy evaluation notes"
    )


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class TerminalSession(BaseModel):
    """Represents an active or historical terminal execution session."""

    session_id: str = Field(
        default_factory=lambda: f"sess_{uuid.uuid4().hex[:12]}",
        description="Unique session identifier",
    )
    shell: TerminalShell = Field(..., description="Shell associated with this session")
    owner_id: str = Field(default="system", description="Owner of this session")
    agent_id: str | None = Field(default=None, description="Agent that owns the session")
    status: SessionStatus = Field(
        default=SessionStatus.ACTIVE, description="Current session state"
    )
    command_count: int = Field(
        default=0, ge=0, description="Number of commands executed in this session"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Session creation timestamp"
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last activity timestamp"
    )
    closed_at: datetime | None = Field(
        default=None, description="Session closure timestamp"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Session metadata tags"
    )


# ---------------------------------------------------------------------------
# Audit Trace
# ---------------------------------------------------------------------------


class TerminalTraceEvent(BaseModel):
    """Immutable audit trace event for terminal operations.

    All terminal execution actions are recorded to this trace for full
    auditability and post-hoc investigation.
    """

    event_id: str = Field(
        default_factory=lambda: f"tevt_{uuid.uuid4().hex[:12]}",
        description="Unique trace event identifier",
    )
    request_id: str | None = Field(
        default=None, description="Associated command request ID"
    )
    session_id: str | None = Field(
        default=None, description="Associated session ID"
    )
    event_type: str = Field(..., description="Trace event type string")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Sanitized, redacted trace details"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )
