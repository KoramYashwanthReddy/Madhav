"""Domain models and data structures for Module 41 — Future Autonomous Intelligence."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AutonomyLevel(StrEnum):
    """Autonomy level hierarchy (Level 0 through Level 5)."""

    MANUAL = "MANUAL"  # Level 0: Reactive only
    ASSISTED = "ASSISTED"  # Level 1: Proposes actions, user executes
    SUPERVISED = "SUPERVISED"  # Level 2: Executes low-risk, asks for sensitive
    DELEGATED = "DELEGATED"  # Level 3: Bounded multi-step missions
    PROACTIVE = "PROACTIVE"  # Level 4: Initiates bounded missions from signals
    HIGH_AUTONOMY = "HIGH_AUTONOMY"  # Level 5: Long-running bounded objectives with full audit/kill-switch


class RiskLevel(StrEnum):
    """Risk severity classification for autonomous actions."""

    LOW = "LOW"  # Read-only, calculation, non-sensitive organization
    MEDIUM = "MEDIUM"  # Normal notifications, draft generation, non-critical updates
    HIGH = "HIGH"  # System modifications, external messages, config updates
    CRITICAL = "CRITICAL"  # Deletions, financial, credentials, security, production changes


class MissionStatus(StrEnum):
    """Mission execution lifecycle states."""

    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    WAITING_FOR_EXTERNAL_EVENT = "WAITING_FOR_EXTERNAL_EVENT"
    REPLANNING = "REPLANNING"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ABORTED = "ABORTED"


class ApprovalStatus(StrEnum):
    """Human approval state for requested actions."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ActionStatus(StrEnum):
    """Status of an individual atomic step action."""

    PLANNED = "PLANNED"
    AUTHORIZED = "AUTHORIZED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class SimulationMode(StrEnum):
    """Autonomy execution environment simulation mode."""

    DRY_RUN = "DRY_RUN"  # Plan and check permissions, no side effects
    SIMULATION = "SIMULATION"  # Execute in mock environment
    LIVE = "LIVE"  # Production execution subject to permission limits


class ResourceBudget(BaseModel):
    """Resource budget constraints governing autonomous execution."""

    max_execution_seconds: int = Field(default=3600, ge=10, le=604800, description="Max runtime limit in seconds")
    max_tokens: int = Field(default=100000, ge=1000, le=10000000, description="Max AI model token count budget")
    max_tool_calls: int = Field(default=50, ge=1, le=1000, description="Max tool invocations permitted")
    max_agent_delegations: int = Field(default=5, ge=0, le=50, description="Max child agent delegations")
    max_files_touched: int = Field(default=20, ge=0, le=500, description="Max filesystem files modified")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max transient failure retries per step")
    max_replans: int = Field(default=3, ge=0, le=10, description="Max replanning cycles permitted")


class AutonomyPolicy(BaseModel):
    """Governance policy controlling permissions, thresholds, and safety rules for autonomy."""

    policy_id: str = Field(default="default_policy", description="Policy identifier")
    owner_id: str = Field(default="user_admin", description="Policy owner entity ID")
    level: AutonomyLevel = Field(default=AutonomyLevel.SUPERVISED, description="Configured autonomy level")
    allowed_actions: list[str] = Field(
        default_factory=lambda: ["read_*", "search_*", "summarize_*", "calculate_*"],
        description="Explicitly allowed action patterns",
    )
    blocked_actions: list[str] = Field(
        default_factory=lambda: ["delete_*", "purge_*", "credential_*", "security_*", "deploy_*"],
        description="Explicitly blocked action patterns",
    )
    require_approval_risk: RiskLevel = Field(
        default=RiskLevel.HIGH, description="Minimum risk level triggering mandatory user approval"
    )
    resource_limits: ResourceBudget = Field(default_factory=ResourceBudget, description="Global budget limits")
    stop_conditions: list[str] = Field(
        default_factory=lambda: ["kill_switch_active", "scope_violation", "budget_exceeded"],
        description="Conditions triggering mandatory mission termination",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(), description="Creation ISO timestamp"
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(), description="Update ISO timestamp"
    )


class Milestone(BaseModel):
    """Individual objective milestone step."""

    milestone_id: str = Field(..., description="Milestone ID")
    objective_id: str = Field(..., description="Parent objective ID")
    name: str = Field(..., description="Milestone title")
    description: str = Field(default="", description="Milestone description")
    success_criteria: str = Field(..., description="Verification criteria for completion")
    status: str = Field(default="PENDING", description="Milestone status (PENDING, IN_PROGRESS, COMPLETED, FAILED)")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")


class Objective(BaseModel):
    """Long-term goal broken down into concrete milestones."""

    objective_id: str = Field(..., description="Objective ID")
    mission_id: str = Field(..., description="Parent mission ID")
    goal: str = Field(..., description="High-level goal statement")
    priority: str = Field(default="NORMAL", description="Priority level (LOW, NORMAL, HIGH, CRITICAL)")
    milestones: list[Milestone] = Field(default_factory=list, description="Associated milestones")
    status: str = Field(default="ACTIVE", description="Objective status")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Overall progress percentage")
    deadline: str | None = Field(default=None, description="ISO timestamp deadline")


class ApprovalRequest(BaseModel):
    """Human-in-the-loop approval request item."""

    approval_id: str = Field(..., description="Unique approval request ID")
    mission_id: str = Field(..., description="Associated mission ID")
    action_name: str = Field(..., description="Proposed action or tool call")
    risk_level: RiskLevel = Field(..., description="Assessed risk level")
    reason: str = Field(..., description="Justification for action requirement")
    impact_summary: str = Field(..., description="Expected side-effects and reversibility assessment")
    requested_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(), description="Creation timestamp"
    )
    expires_at: str = Field(..., description="Expiration timestamp (approvals expire after timeout)")
    status: ApprovalStatus = Field(default=ApprovalStatus.PENDING, description="Approval status")
    approved_by: str | None = Field(default=None, description="Approving user ID if approved")
    decision_at: str | None = Field(default=None, description="Decision timestamp")


class MissionAction(BaseModel):
    """Atomic action step executed within a mission."""

    action_id: str = Field(..., description="Action ID")
    mission_id: str = Field(..., description="Parent mission ID")
    step_number: int = Field(..., description="1-indexed sequence number")
    tool_id: str = Field(..., description="Target tool ID in Tool Registry")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Action arguments")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Assessed risk level")
    status: ActionStatus = Field(default=ActionStatus.PLANNED, description="Action execution status")
    result: dict[str, Any] | None = Field(default=None, description="Output payload if executed")
    verification_evidence: str | None = Field(default=None, description="Empirical evidence validating outcome")
    error: str | None = Field(default=None, description="Error message if failed")
    started_at: str | None = Field(default=None, description="Execution start timestamp")
    completed_at: str | None = Field(default=None, description="Execution completion timestamp")


class Mission(BaseModel):
    """Core Mission entity orchestrating multi-step autonomous execution."""

    mission_id: str = Field(..., description="Unique mission ID")
    owner_id: str = Field(default="user_admin", description="Mission owner user ID")
    title: str = Field(..., description="Mission title")
    objective: str = Field(..., description="Detailed objective statement")
    status: MissionStatus = Field(default=MissionStatus.DRAFT, description="Current mission status")
    autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.SUPERVISED, description="Mission autonomy level")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Overall mission risk classification")
    allowed_scope: list[str] = Field(
        default_factory=lambda: ["data/*", "artifacts/*", "docs/*"],
        description="Allowed resource paths/domains",
    )
    success_criteria: list[str] = Field(default_factory=list, description="Explicit verification criteria")
    stop_conditions: list[str] = Field(default_factory=list, description="Custom mission stop triggers")
    budget: ResourceBudget = Field(default_factory=ResourceBudget, description="Allocated budget limits")
    used_budget: dict[str, Any] = Field(
        default_factory=lambda: {
            "execution_seconds": 0,
            "tokens": 0,
            "tool_calls": 0,
            "agent_delegations": 0,
            "files_touched": 0,
            "retries": 0,
            "replans": 0,
        },
        description="Actual resource usage metrics",
    )
    actions: list[MissionAction] = Field(default_factory=list, description="Executed or planned action steps")
    approvals: list[ApprovalRequest] = Field(default_factory=list, description="Pending or resolved approvals")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(), description="ISO creation timestamp"
    )
    expires_at: str | None = Field(default=None, description="ISO expiration deadline timestamp")


class MissionResult(BaseModel):
    """Final mission verification summary and report."""

    mission_id: str = Field(..., description="Mission ID")
    status: MissionStatus = Field(..., description="Final mission status")
    summary: str = Field(..., description="Concise human-readable summary")
    completed_steps_count: int = Field(default=0, description="Total succeeded steps")
    failed_steps_count: int = Field(default=0, description="Total failed steps")
    evidence: list[str] = Field(default_factory=list, description="Empirical evidence supporting completion")
    artifacts_produced: list[str] = Field(default_factory=list, description="Paths/URIs of created artifacts")
    verification_passed: bool = Field(default=False, description="Whether final verification succeeded")


class AutonomousExecutionRequest(BaseModel):
    """Execution request context evaluated by Module 15 Security."""

    mission_id: str = Field(..., description="Mission ID")
    action_name: str = Field(..., description="Target tool or system action")
    target_resource: str = Field(..., description="Resource string (path, API, etc.)")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    autonomy_level: AutonomyLevel = Field(..., description="Active autonomy level")
    risk_level: RiskLevel = Field(..., description="Assessed action risk level")


class AutonomyHealth(BaseModel):
    """Telemetry diagnostic snapshot for Module 41 Autonomy subsystem."""

    active_missions: int = Field(default=0, description="Currently running or queued missions")
    completed_missions: int = Field(default=0, description="Total completed missions")
    failed_missions: int = Field(default=0, description="Total failed missions")
    blocked_missions: int = Field(default=0, description="Missions currently blocked by security or policy")
    pending_approvals: int = Field(default=0, description="Unresolved pending approval requests")
    kill_switch_active: bool = Field(default=False, description="Global emergency autonomy kill-switch state")
    circuit_breaker_tripped: bool = Field(default=False, description="Mission circuit breaker status")
