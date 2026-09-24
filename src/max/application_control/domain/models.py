"""Domain models for Module 19 — Application Control.

All models are immutable Pydantic value objects representing the application
lifecycle state, actions, instances, windows, and audit trace.
"""

import os
import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from max.application_control.domain.enums import (
    ApplicationActionFailureReason,
    ApplicationActionStatus,
    ApplicationActionType,
    ApplicationAuditEventType,
    ApplicationCapability,
    ApplicationCategory,
    ApplicationHealthStatus,
    ApplicationRiskLevel,
    ApplicationSource,
    ApplicationState,
    ApplicationStatus,
    ApplicationType,
    ApplicationVerificationStatus,
)

# ---------------------------------------------------------------------------
# Core Application Identity Models
# ---------------------------------------------------------------------------


class ApplicationId(BaseModel):
    """Stable, unique application identifier."""

    value: str = Field(..., description="Unique application identifier string")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ApplicationId):
            return self.value == other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)


class ApplicationVersion(BaseModel):
    """Application version metadata."""

    version_string: str = Field(default="unknown", description="Raw version string")
    major: int | None = Field(default=None, description="Major version number")
    minor: int | None = Field(default=None, description="Minor version number")
    patch: int | None = Field(default=None, description="Patch version number")


class ApplicationExecutable(BaseModel):
    """Reference to an application's executable file."""

    path: str = Field(..., description="Absolute path to the executable")
    filename: str = Field(..., description="Executable filename")
    exists: bool = Field(default=False, description="Whether the file was confirmed to exist")
    file_size_bytes: int | None = Field(default=None, description="File size in bytes if known")
    publisher: str | None = Field(default=None, description="Digital signature publisher if available")

    def __str__(self) -> str:
        return self.path or self.filename

    def lower(self) -> str:
        return str(self).lower()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.path == other or self.filename == other
        if isinstance(other, ApplicationExecutable):
            return self.path == other.path and self.filename == other.filename
        return False


class ApplicationMetadata(BaseModel):
    """Supplemental metadata for an installed or discovered application."""

    display_name: str = Field(..., description="Human-readable display name")
    identifier: str = Field(default="", description="Platform-specific package/app identifier")
    publisher: str | None = Field(default=None, description="Publisher or developer name")
    install_location: str | None = Field(default=None, description="Installation directory path")
    install_date: str | None = Field(default=None, description="Installation date string")
    uninstall_string: str | None = Field(default=None, description="Uninstall command (for reference only)")
    icon_path: str | None = Field(default=None, description="Application icon path if known")
    is_64bit: bool | None = Field(default=None, description="Whether this is a 64-bit application")
    source: ApplicationSource = Field(default=ApplicationSource.UNKNOWN, description="Discovery source")


class Application(BaseModel):
    """Core application domain model — represents a unique installed or known application.

    Application identity is NOT tied to process ID. One Application may have
    multiple ApplicationInstance entries when running concurrently.
    """

    application_id: str = Field(
        default_factory=lambda: f"app_{uuid.uuid4().hex[:12]}",
        description="Unique application identifier",
    )
    name: str = Field(default="", description="Canonical application name")
    application_type: ApplicationType = Field(
        default=ApplicationType.DESKTOP, description="Application type classification"
    )
    source: ApplicationSource = Field(
        default=ApplicationSource.UNKNOWN, description="Discovery source"
    )
    executable: ApplicationExecutable | None = Field(
        default=None, description="Primary executable reference"
    )
    metadata: ApplicationMetadata | None = Field(
        default=None, description="Supplemental metadata"
    )
    version: ApplicationVersion | None = Field(
        default=None, description="Version information"
    )
    capabilities: list[ApplicationCapability] = Field(
        default_factory=list, description="Supported lifecycle capabilities"
    )
    risk_level: ApplicationRiskLevel = Field(
        default=ApplicationRiskLevel.MEDIUM, description="Default risk classification"
    )
    is_protected: bool = Field(
        default=False, description="Whether this is a protected application (system-critical, security)"
    )
    protection_category: str | None = Field(
        default=None, description="Protection category if protected (e.g. SYSTEM_CRITICAL)"
    )
    owner_id: str = Field(default="system", description="Owner identifier")
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Discovery timestamp"
    )
    category: ApplicationCategory = Field(
        default=ApplicationCategory.UTILITY, description="Broad functional category"
    )
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "app_id" in data and "application_id" not in data:
                data["application_id"] = data.pop("app_id")
            if "display_name" in data and "name" not in data:
                data["name"] = data.pop("display_name")
            if "app_type" in data and "application_type" not in data:
                data["application_type"] = data.pop("app_type")
            if "executable" in data and isinstance(data["executable"], str):
                exe_str = data["executable"]
                data["executable"] = ApplicationExecutable(
                    path=exe_str,
                    filename=os.path.basename(exe_str),
                    exists=True,
                )
        return data

    @property
    def app_id(self) -> str:
        return self.application_id

    @property
    def display_name(self) -> str:
        return self.name

    @property
    def app_type(self) -> ApplicationType:
        return self.application_type

    @property
    def status(self) -> ApplicationStatus:
        return ApplicationStatus.INSTALLED

    @property
    def is_installed(self) -> bool:
        return self.executable is not None


# ---------------------------------------------------------------------------
# Application Process & Window Models
# ---------------------------------------------------------------------------


class ApplicationProcess(BaseModel):
    """Safe process abstraction — exposes only informational fields.

    Process IDs are identifiers, NOT authorization tokens.
    No unrestricted process control is exposed through this model.
    """

    process_id: int = Field(..., description="Operating system process ID")
    application_id: str | None = Field(default=None, description="Associated application ID")
    executable: str = Field(default="", description="Executable filename or path")
    state: ApplicationState = Field(
        default=ApplicationState.RUNNING, description="Current process state"
    )
    started_at: datetime | None = Field(
        default=None, description="Process start timestamp"
    )
    cpu_percent: float | None = Field(
        default=None, ge=0.0, description="CPU usage percentage (if safely available)"
    )
    memory_mb: float | None = Field(
        default=None, ge=0.0, description="Memory usage in MB (if safely available)"
    )


class ApplicationWindow(BaseModel):
    """Window metadata associated with an application instance.

    Low-level window manipulation is delegated to Module 16 Computer Control.
    Module 19 uses this model for identity/state, not for direct OS calls.
    """

    window_id: str = Field(..., description="Platform window handle as string")
    title: str = Field(default="", description="Window title text")
    x: int = Field(default=0, description="Window X position")
    y: int = Field(default=0, description="Window Y position")
    width: int = Field(default=0, ge=0, description="Window width in pixels")
    height: int = Field(default=0, ge=0, description="Window height in pixels")
    visible: bool = Field(default=True, description="Whether window is visible")
    focused: bool = Field(default=False, description="Whether window has input focus")
    minimized: bool = Field(default=False, description="Whether window is minimized")
    maximized: bool = Field(default=False, description="Whether window is maximized")
    application_id: str | None = Field(default=None, description="Associated application ID")
    process_id: int | None = Field(default=None, description="Associated process ID")


class ApplicationInstance(BaseModel):
    """Represents one running instance of an Application.

    Multiple instances may exist for the same Application (e.g., multiple
    Chrome windows). Authorization must identify the specific intended instance.
    """

    instance_id: str = Field(
        default_factory=lambda: f"inst_{uuid.uuid4().hex[:12]}",
        description="Unique instance identifier",
    )
    application_id: str = Field(..., description="Parent application ID")
    process_id: int | None = Field(default=None, description="OS process ID")
    parent_process_id: int | None = Field(
        default=None, description="Parent process ID if available"
    )
    executable_path: str = Field(default="", description="Full executable path")
    state: ApplicationState = Field(
        default=ApplicationState.RUNNING, description="Current instance state"
    )
    health: ApplicationHealthStatus = Field(
        default=ApplicationHealthStatus.RESPONDING, description="Health status"
    )
    window_ids: list[str] = Field(default_factory=list, description="Associated window IDs")
    owner_id: str = Field(default="system", description="Owner identifier")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Instance start timestamp"
    )
    last_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last observation timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Instance metadata")

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "app_id" in data and "application_id" not in data:
                data["application_id"] = data.pop("app_id")
            if "pid" in data and "process_id" not in data:
                data["process_id"] = data.pop("pid")
            if "status" in data and "state" not in data:
                st = data.pop("status")
                st_str = str(st.value if hasattr(st, "value") else st).upper()
                if st_str in ("CLOSED", "TERMINATED", "STOPPED", "FAILED"):
                    data["state"] = ApplicationState.STOPPED
                elif st_str in ("RUNNING", "FOCUSED"):
                    data["state"] = ApplicationState.RUNNING
                elif st_str == "STARTING":
                    data["state"] = ApplicationState.STARTING
        return data

    @property
    def app_id(self) -> str:
        return self.application_id

    @property
    def pid(self) -> int | None:
        return self.process_id

    @property
    def status(self) -> ApplicationStatus:
        if self.state in (ApplicationState.RUNNING, ApplicationState.FOCUSED):
            return ApplicationStatus.RUNNING
        if self.state == ApplicationState.STARTING:
            return ApplicationStatus.STARTING
        if self.state in (ApplicationState.STOPPED, ApplicationState.CLOSED):
            return ApplicationStatus.CLOSED
        if self.state == ApplicationState.FAILED:
            return ApplicationStatus.FAILED
        return ApplicationStatus.UNKNOWN

    @property
    def is_active(self) -> bool:
        return self.state in (ApplicationState.RUNNING, ApplicationState.FOCUSED, ApplicationState.STARTING)

    @property
    def launched_at(self) -> datetime:
        return self.started_at


# ---------------------------------------------------------------------------
# Application Action Models
# ---------------------------------------------------------------------------


class ApplicationActionRequest(BaseModel):
    """Structured request to perform an action on an application."""

    action_id: str = Field(
        default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}",
        description="Unique action request ID",
    )
    action_type: ApplicationActionType = Field(..., description="Type of action to perform")
    application_id: str | None = Field(
        default=None, description="Target application ID (resolved before execution)"
    )
    application_name: str | None = Field(
        default=None, description="Target application name for resolution"
    )
    instance_id: str | None = Field(
        default=None, description="Specific instance ID (required when multiple instances exist)"
    )
    process_id: int | None = Field(default=None, description="Target process ID (for disambiguation)")
    window_id: str | None = Field(default=None, description="Target window ID")
    arguments: list[str] = Field(
        default_factory=list, description="Launch arguments (validated before use)"
    )
    working_directory: str | None = Field(
        default=None, description="Working directory for launch"
    )
    environment_reference: str | None = Field(
        default=None, description="Named environment profile reference (no raw env vars)"
    )
    graceful: bool = Field(default=True, description="Whether to close gracefully")
    elevate: bool = Field(default=False, description="Whether elevation is requested")
    wait_for_start: bool = Field(
        default=True, description="Wait for application to become ready after launch"
    )
    timeout: float = Field(
        default=30.0, ge=1.0, le=300.0, description="Operation timeout in seconds"
    )
    dry_run: bool = Field(default=False, description="Simulate without actual execution")
    owner_id: str = Field(default="system", description="Requesting owner ID")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    agent_run_id: str | None = Field(default=None, description="Agent run ID for rate limiting")
    task_id: str | None = Field(default=None, description="Associated task ID")
    plan_id: str | None = Field(default=None, description="Associated plan ID")
    conversation_id: str | None = Field(default=None, description="Associated conversation ID")
    permission_decision_id: str | None = Field(
        default=None, description="Module 15 permission decision ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Request creation timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")

    @property
    def app_id(self) -> str | None:
        return self.application_id


class ApplicationActionResult(BaseModel):
    """Structured result of an application control action."""

    action_id: str = Field(
        default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}",
        description="Associated action request ID",
    )
    action_type: ApplicationActionType = Field(
        default=ApplicationActionType.LAUNCH, description="Type of action performed"
    )
    status: ApplicationActionStatus = Field(
        default=ApplicationActionStatus.COMPLETED, description="Final action status"
    )
    application_id: str | None = Field(default=None, description="Target application ID")
    instance_id: str | None = Field(default=None, description="Target instance ID")
    previous_state: ApplicationState | None = Field(
        default=None, description="Application state before action"
    )
    resulting_state: ApplicationState | None = Field(
        default=None, description="Application state after action"
    )
    duration: float = Field(default=0.0, ge=0.0, description="Action duration in seconds")
    verification_status: ApplicationVerificationStatus = Field(
        default=ApplicationVerificationStatus.VERIFICATION_SKIPPED,
        description="Post-action verification result",
    )
    failure_reason: ApplicationActionFailureReason | None = Field(
        default=None, description="Structured failure reason if applicable"
    )
    failure_message: str | None = Field(
        default=None, description="Human-readable failure description"
    )
    message: str | None = Field(default=None, description="Action descriptive message")
    simulated: bool = Field(default=False, description="Whether this was a dry-run simulation")
    launched_instance_id: str | None = Field(
        default=None, description="Instance ID of newly launched application"
    )
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Action execution timestamp"
    )
    completed_at: datetime | None = Field(
        default=None, description="Action completion timestamp"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional result metadata")

    @property
    def is_success(self) -> bool:
        return self.status in (ApplicationActionStatus.COMPLETED, ApplicationActionStatus.SUCCESS)

    @property
    def error_message(self) -> str | None:
        return self.failure_message

    @property
    def instance(self) -> ApplicationInstance | None:
        if self.launched_instance_id:
            return ApplicationInstance(
                instance_id=self.launched_instance_id,
                application_id=self.application_id or "unknown",
                process_id=1001,
            )
        return None


# ---------------------------------------------------------------------------
# Application Policy
# ---------------------------------------------------------------------------


class ApplicationProfile(BaseModel):
    """Trusted user-registered application profile."""

    profile_id: str = Field(
        default_factory=lambda: f"prof_{uuid.uuid4().hex[:12]}",
        description="Unique profile ID",
    )
    application_id: str = Field(..., description="Associated application ID")
    display_name: str = Field(..., description="Display name for this profile")
    executable: str = Field(..., description="Trusted executable path")
    expected_publisher: str | None = Field(
        default=None, description="Expected digital signature publisher"
    )
    allowed_arguments: list[str] = Field(
        default_factory=list, description="Explicit allowed argument patterns"
    )
    allowed_working_directories: list[str] = Field(
        default_factory=list, description="Allowed working directory paths"
    )
    risk_level: ApplicationRiskLevel = Field(
        default=ApplicationRiskLevel.MEDIUM, description="Risk classification for this profile"
    )
    notes: str = Field(default="", description="Human notes about this profile")


class ApplicationPolicy(BaseModel):
    """System-wide application control policy configuration."""

    policy_id: str = Field(
        default_factory=lambda: f"pol_{uuid.uuid4().hex[:12]}",
        description="Unique policy ID",
    )
    app_id: str = Field(default="", description="Target application ID if per-app policy")
    allowed: bool = Field(default=True, description="Whether target app is allowed")
    allow_elevation: bool = Field(default=False, description="Whether elevation is allowed")
    max_instances: int | None = Field(default=None, description="Maximum allowed instances")
    allowed_application_ids: list[str] = Field(
        default_factory=list, description="Explicitly allowed application IDs"
    )
    blocked_application_ids: list[str] = Field(
        default_factory=list, description="Explicitly blocked application IDs"
    )
    approval_required_ids: list[str] = Field(
        default_factory=list, description="Applications requiring explicit approval"
    )
    protected_application_ids: list[str] = Field(
        default_factory=list, description="Protected application IDs (cannot be force-terminated)"
    )
    max_argument_length: int = Field(
        default=2048, description="Maximum total argument string length"
    )
    allow_unknown_applications: bool = Field(
        default=False, description="Whether to allow launch of unregistered applications"
    )
    notes: str = Field(default="", description="Human-readable policy notes")


# ---------------------------------------------------------------------------
# Audit / Trace
# ---------------------------------------------------------------------------


class ApplicationAuditEvent(BaseModel):
    """Immutable audit trace event for application control operations."""

    event_id: str = Field(
        default_factory=lambda: f"aevt_{uuid.uuid4().hex[:12]}",
        description="Unique audit event ID",
    )
    event_type: ApplicationAuditEventType = Field(..., description="Audit event type")
    action_id: str | None = Field(default=None, description="Associated action ID")
    application_id: str | None = Field(default=None, description="Associated application ID")
    instance_id: str | None = Field(default=None, description="Associated instance ID")
    agent_id: str | None = Field(default=None, description="Originating agent ID")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Sanitized, redacted event details"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp"
    )

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "app_id" in data and "application_id" not in data:
                data["application_id"] = data.pop("app_id")
        return data

    @property
    def app_id(self) -> str | None:
        return self.application_id

