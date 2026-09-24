"""Domain enums for Module 30 — Proactive Intelligence Engine."""

from enum import IntEnum, StrEnum


class SignalSource(StrEnum):
    """Source categories for proactive signals."""

    CONVERSATION = "CONVERSATION"
    MEMORY = "MEMORY"
    KNOWLEDGE = "KNOWLEDGE"
    SCHEDULER = "SCHEDULER"
    EXTERNAL_INTEGRATION = "EXTERNAL_INTEGRATION"
    EMAIL = "EMAIL"
    CALENDAR = "CALENDAR"
    GITHUB = "GITHUB"
    BROWSER = "BROWSER"
    SYSTEM = "SYSTEM"
    APPLICATION = "APPLICATION"
    FILESYSTEM = "FILESYSTEM"
    TASK = "TASK"
    AGENT = "AGENT"
    USER_FEEDBACK = "USER_FEEDBACK"
    OTHER = "OTHER"


class DecisionType(StrEnum):
    """Decision outputs for proactive evaluation."""

    STAY_SILENT = "STAY_SILENT"
    NOTIFY = "NOTIFY"
    ASK_USER = "ASK_USER"
    CREATE_TASK = "CREATE_TASK"
    TRIGGER_AUTOMATION = "TRIGGER_AUTOMATION"
    RECOMMEND = "RECOMMEND"
    EXECUTE_ACTION = "EXECUTE_ACTION"


class ActionType(StrEnum):
    """Types of proactive actions."""

    STAY_SILENT = "STAY_SILENT"
    NOTIFY = "NOTIFY"
    ASK_USER = "ASK_USER"
    RECOMMEND = "RECOMMEND"
    CREATE_TASK = "CREATE_TASK"
    TRIGGER_AUTOMATION = "TRIGGER_AUTOMATION"
    EXECUTE_ACTION = "EXECUTE_ACTION"


class ActionStatus(StrEnum):
    """Status states for proactive actions."""

    PENDING = "PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ProactiveMode(StrEnum):
    """Operating modes for proactive intelligence."""

    PASSIVE = "PASSIVE"
    NORMAL = "NORMAL"
    PROACTIVE = "PROACTIVE"
    AUTONOMOUS = "AUTONOMOUS"


class AutonomyLevel(IntEnum):
    """Autonomy levels for proactive operations."""

    LEVEL_0 = 0  # Observe only
    LEVEL_1 = 1  # Notify
    LEVEL_2 = 2  # Recommend
    LEVEL_3 = 3  # Create task
    LEVEL_4 = 4  # Execute low-risk authorized action
    LEVEL_5 = 5  # Multi-step autonomous workflow


class UserState(StrEnum):
    """User availability and attention context state."""

    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    FOCUSED = "FOCUSED"
    AWAY = "AWAY"
    SLEEPING = "SLEEPING"
    DO_NOT_DISTURB = "DO_NOT_DISTURB"
    UNKNOWN = "UNKNOWN"


class ImportanceLevel(StrEnum):
    """Importance classification for candidates."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class UrgencyLevel(StrEnum):
    """Urgency classification for candidates."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AttentionCost(StrEnum):
    """Attention cost of user interruption."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FeedbackType(StrEnum):
    """User feedback classification for proactive decisions."""

    HELPFUL = "HELPFUL"
    NOT_HELPFUL = "NOT_HELPFUL"
    TOO_FREQUENT = "TOO_FREQUENT"
    DONT_NOTIFY_CATEGORY = "DONT_NOTIFY_CATEGORY"
    ALWAYS_NOTIFY_CATEGORY = "ALWAYS_NOTIFY_CATEGORY"
    AUTOMATE_CATEGORY = "AUTOMATE_CATEGORY"
    NEVER_AUTOMATE_CATEGORY = "NEVER_AUTOMATE_CATEGORY"


class RulePriority(StrEnum):
    """Priority ranks for proactive rules."""

    SECURITY = "SECURITY"
    USER_EXPLICIT = "USER_EXPLICIT"
    SYSTEM = "SYSTEM"
    AUTOMATION = "AUTOMATION"
    DEFAULT = "DEFAULT"


class RuleStatus(StrEnum):
    """Lifecycle status for proactive rules."""

    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"
