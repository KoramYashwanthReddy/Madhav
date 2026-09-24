"""Enumerations for Module 27 — Notification System."""

from enum import Enum


class NotificationStatus(str, Enum):
    """Lifecycle states of a Notification."""

    CREATED = "CREATED"
    QUEUED = "QUEUED"
    ROUTING = "ROUTING"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"

    # Failure / Terminal paths
    DELIVERY_FAILED = "DELIVERY_FAILED"
    RETRYING = "RETRYING"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUPPRESSED = "SUPPRESSED"


class NotificationCategory(str, Enum):
    """Extensible classification categories for notifications."""

    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"
    TASK = "TASK"
    REMINDER = "REMINDER"
    UPDATE = "UPDATE"
    MESSAGE = "MESSAGE"
    AI = "AI"
    DEVELOPER = "DEVELOPER"
    DOCUMENT = "DOCUMENT"
    AUTOMATION = "AUTOMATION"
    INTEGRATION = "INTEGRATION"


class NotificationSeverity(str, Enum):
    """Descriptive severity metadata."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationPriority(str, Enum):
    """Delivery priority determining routing order."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationChannelType(str, Enum):
    """Provider-neutral delivery channel types."""

    IN_APP = "IN_APP"
    DESKTOP = "DESKTOP"
    EMAIL = "EMAIL"
    SPEECH = "SPEECH"
    PUSH = "PUSH"
    WEB = "WEB"
    MOBILE = "MOBILE"


class NotificationSourceType(str, Enum):
    """Origin generator of a notification request."""

    TASK_ENGINE = "TASK_ENGINE"
    AGENT_ENGINE = "AGENT_ENGINE"
    SECURITY = "SECURITY"
    GITHUB = "GITHUB"
    WEB_INTELLIGENCE = "WEB_INTELLIGENCE"
    DOCUMENT = "DOCUMENT"
    SYSTEM = "SYSTEM"
    USER = "USER"
    AUTOMATION = "AUTOMATION"


class NotificationActionType(str, Enum):
    """Action intent classifications for actionable notifications."""

    URL = "URL"
    COMMAND = "COMMAND"
    DISMISS = "DISMISS"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    INTENT = "INTENT"


class NotificationSensitivity(str, Enum):
    """Privacy and security sensitivity classification for content protection."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    PRIVATE = "PRIVATE"
    SENSITIVE = "SENSITIVE"
    HIGHLY_SENSITIVE = "HIGHLY_SENSITIVE"


class NotificationDeliveryStatus(str, Enum):
    """Individual per-channel delivery attempt status."""

    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NotificationReadState(str, Enum):
    """Read & acknowledgement state of a notification."""

    UNREAD = "UNREAD"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    DISMISSED = "DISMISSED"


class NotificationEventType(str, Enum):
    """Structured observable audit event types."""

    NOTIFICATION_CREATED = "notification_created"
    NOTIFICATION_QUEUED = "notification_queued"
    NOTIFICATION_SUPPRESSED = "notification_suppressed"
    NOTIFICATION_ROUTED = "notification_routed"
    NOTIFICATION_DELIVERY_STARTED = "notification_delivery_started"
    NOTIFICATION_DELIVERED = "notification_delivered"
    NOTIFICATION_DELIVERY_FAILED = "notification_delivery_failed"
    NOTIFICATION_RETRY_SCHEDULED = "notification_retry_scheduled"
    NOTIFICATION_CANCELLED = "notification_cancelled"
    NOTIFICATION_READ = "notification_read"
    NOTIFICATION_ACKNOWLEDGED = "notification_acknowledged"
    NOTIFICATION_EXPIRED = "notification_expired"
    NOTIFICATION_GROUPED = "notification_grouped"
    NOTIFICATION_DEDUPLICATED = "notification_deduplicated"
    NOTIFICATION_RATE_LIMITED = "notification_rate_limited"
