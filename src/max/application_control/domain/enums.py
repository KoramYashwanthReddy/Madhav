"""Domain enumerations for Module 19 — Application Control."""

from enum import StrEnum


class ApplicationType(StrEnum):
    """Classification of an application's interaction model."""

    DESKTOP = "DESKTOP"
    SYSTEM = "SYSTEM"
    CONSOLE = "CONSOLE"
    SERVICE = "SERVICE"
    BACKGROUND = "BACKGROUND"
    UNKNOWN = "UNKNOWN"


class ApplicationSource(StrEnum):
    """Origin/discovery source for an application entry."""

    START_MENU = "START_MENU"
    DESKTOP = "DESKTOP"
    INSTALLED_APPLICATION = "INSTALLED_APPLICATION"
    RUNNING_PROCESS = "RUNNING_PROCESS"
    USER_PROVIDED = "USER_PROVIDED"
    SYSTEM = "SYSTEM"
    UNKNOWN = "UNKNOWN"


class ApplicationState(StrEnum):
    """Lifecycle and UI state of an application or instance."""

    NOT_RUNNING = "NOT_RUNNING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FOCUSED = "FOCUSED"
    MINIMIZED = "MINIMIZED"
    MAXIMIZED = "MAXIMIZED"
    BACKGROUND = "BACKGROUND"
    NOT_RESPONDING = "NOT_RESPONDING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ApplicationHealthStatus(StrEnum):
    """Basic health state of a running application."""

    RESPONDING = "RESPONDING"
    NOT_RESPONDING = "NOT_RESPONDING"
    UNKNOWN = "UNKNOWN"


class ApplicationActionType(StrEnum):
    """Action types that can be performed on applications."""

    DISCOVER = "DISCOVER"
    INSPECT = "INSPECT"
    LAUNCH = "LAUNCH"
    FOCUS = "FOCUS"
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"
    RESTORE = "RESTORE"
    CLOSE = "CLOSE"
    FORCE_TERMINATE = "FORCE_TERMINATE"
    RESTART = "RESTART"


class ApplicationActionStatus(StrEnum):
    """Lifecycle state of an application action request."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    SUCCESS = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    SIMULATED = "SIMULATED"


class ApplicationActionFailureReason(StrEnum):
    """Structured failure taxonomy for application control operations."""

    SUBSYSTEM_DISABLED = "SUBSYSTEM_DISABLED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    PROTECTED_APPLICATION = "PROTECTED_APPLICATION"
    APPLICATION_NOT_FOUND = "APPLICATION_NOT_FOUND"
    APPLICATION_AMBIGUOUS = "APPLICATION_AMBIGUOUS"
    APPLICATION_NOT_INSTALLED = "APPLICATION_NOT_INSTALLED"
    APPLICATION_NOT_RUNNING = "APPLICATION_NOT_RUNNING"
    APPLICATION_ALREADY_RUNNING = "APPLICATION_ALREADY_RUNNING"
    APPLICATION_NOT_RESPONDING = "APPLICATION_NOT_RESPONDING"
    INSTANCE_NOT_FOUND = "INSTANCE_NOT_FOUND"
    INSTANCE_AMBIGUOUS = "INSTANCE_AMBIGUOUS"
    WINDOW_NOT_FOUND = "WINDOW_NOT_FOUND"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INVALID_EXECUTABLE = "INVALID_EXECUTABLE"
    INVALID_ARGUMENTS = "INVALID_ARGUMENTS"
    INVALID_WORKING_DIRECTORY = "INVALID_WORKING_DIRECTORY"
    PATH_NOT_ALLOWED = "PATH_NOT_ALLOWED"
    STARTUP_TIMEOUT = "STARTUP_TIMEOUT"
    CLOSE_TIMEOUT = "CLOSE_TIMEOUT"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ApplicationCapability(StrEnum):
    """Descriptive capability flags for application control operations.

    These are descriptive, NOT permissions. Module 15 remains authoritative.
    """

    DISCOVER = "DISCOVER"
    LAUNCH = "LAUNCH"
    FOCUS = "FOCUS"
    MINIMIZE = "MINIMIZE"
    MAXIMIZE = "MAXIMIZE"
    RESTORE = "RESTORE"
    CLOSE = "CLOSE"
    FORCE_TERMINATE = "FORCE_TERMINATE"
    RESTART = "RESTART"
    INSPECT_STATUS = "INSPECT_STATUS"


class ApplicationRiskLevel(StrEnum):
    """Risk classification for application actions (informational; Module 15 is authoritative)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ApplicationVerificationStatus(StrEnum):
    """Result of post-action verification."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    VERIFICATION_SKIPPED = "VERIFICATION_SKIPPED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class ApplicationCategory(StrEnum):
    """Broad functional category of an application."""

    DEVELOPMENT = "DEVELOPMENT"
    PRODUCTIVITY = "PRODUCTIVITY"
    BROWSER = "BROWSER"
    MEDIA = "MEDIA"
    COMMUNICATION = "COMMUNICATION"
    UTILITY = "UTILITY"
    SYSTEM = "SYSTEM"
    GAME = "GAME"
    OTHER = "OTHER"


class ApplicationStatus(StrEnum):
    """Status state of an application or instance."""

    INSTALLED = "INSTALLED"
    NOT_RUNNING = "NOT_RUNNING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FOCUSED = "FOCUSED"
    CLOSED = "CLOSED"
    TERMINATED = "TERMINATED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


class ApplicationAuditEventType(StrEnum):
    """Audit event types for the Application Control trace log."""

    DISCOVERED = "DISCOVERED"
    RESOLVED = "RESOLVED"
    ACTION_REQUESTED = "ACTION_REQUESTED"
    LAUNCHED = "LAUNCHED"
    LAUNCH_FAILED = "LAUNCH_FAILED"
    FOCUSED = "FOCUSED"
    MINIMIZED = "MINIMIZED"
    MAXIMIZED = "MAXIMIZED"
    RESTORED = "RESTORED"
    CLOSED = "CLOSED"
    TERMINATED = "TERMINATED"
    RESTARTED = "RESTARTED"
    POLICY_UPDATED = "POLICY_UPDATED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"

