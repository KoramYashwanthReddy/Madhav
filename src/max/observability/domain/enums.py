"""Domain Enums for Module 33 — Observability & Audit."""

from enum import StrEnum


class SpanKind(StrEnum):
    """OpenTelemetry-compatible span kinds."""

    INTERNAL = "INTERNAL"
    SERVER = "SERVER"
    CLIENT = "CLIENT"
    PRODUCER = "PRODUCER"
    CONSUMER = "CONSUMER"


class SpanStatus(StrEnum):
    """Status codes for execution spans."""

    UNSET = "UNSET"
    OK = "OK"
    ERROR = "ERROR"


class SpanType(StrEnum):
    """Categorized execution span types across Max modules."""

    HTTP_REQUEST = "HTTP_REQUEST"
    CONVERSATION = "CONVERSATION"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    CONTEXT_BUILD = "CONTEXT_BUILD"
    MEMORY_ACCESS = "MEMORY_ACCESS"
    KNOWLEDGE_ACCESS = "KNOWLEDGE_ACCESS"
    RETRIEVAL = "RETRIEVAL"
    REASONING = "REASONING"
    TASK = "TASK"
    AGENT = "AGENT"
    TOOL = "TOOL"
    PERMISSION_CHECK = "PERMISSION_CHECK"
    FILESYSTEM = "FILESYSTEM"
    TERMINAL = "TERMINAL"
    APPLICATION = "APPLICATION"
    BROWSER = "BROWSER"
    WEB_RESEARCH = "WEB_RESEARCH"
    DOCUMENT = "DOCUMENT"
    VISION = "VISION"
    SPEECH = "SPEECH"
    NOTIFICATION = "NOTIFICATION"
    SCHEDULER = "SCHEDULER"
    AUTOMATION = "AUTOMATION"
    INTEGRATION = "INTEGRATION"
    EVALUATION = "EVALUATION"
    DATABASE = "DATABASE"
    CACHE = "CACHE"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    CUSTOM = "CUSTOM"


class LogLevel(StrEnum):
    """Standardized logging severity levels."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditEventType(StrEnum):
    """Categorized audit event domain types."""

    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    PERMISSION = "PERMISSION"
    APPROVAL = "APPROVAL"
    SECURITY = "SECURITY"
    MEMORY = "MEMORY"
    KNOWLEDGE = "KNOWLEDGE"
    CONVERSATION = "CONVERSATION"
    TASK = "TASK"
    AGENT = "AGENT"
    TOOL = "TOOL"
    FILE = "FILE"
    TERMINAL = "TERMINAL"
    APPLICATION = "APPLICATION"
    BROWSER = "BROWSER"
    INTEGRATION = "INTEGRATION"
    AUTOMATION = "AUTOMATION"
    SCHEDULER = "SCHEDULER"
    NOTIFICATION = "NOTIFICATION"
    MODEL = "MODEL"
    CONFIGURATION = "CONFIGURATION"
    ADMIN = "ADMIN"
    EVALUATION = "EVALUATION"
    DATA = "DATA"
    SYSTEM = "SYSTEM"
    CUSTOM = "CUSTOM"


class AuditActor(StrEnum):
    """Actors responsible for initiating audited actions."""

    USER = "USER"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"
    TOOL = "TOOL"
    SCHEDULER = "SCHEDULER"
    AUTOMATION = "AUTOMATION"
    INTEGRATION = "INTEGRATION"
    ADMIN = "ADMIN"
    MODEL = "MODEL"
    EXTERNAL_SYSTEM = "EXTERNAL_SYSTEM"
    UNKNOWN = "UNKNOWN"


class AuditOutcome(StrEnum):
    """Audit action result outcomes."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    DENIED = "DENIED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    PARTIAL = "PARTIAL"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    UNKNOWN = "UNKNOWN"


class AuditSeverity(StrEnum):
    """Severity classification for security and audit events."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AuditCategory(StrEnum):
    """Broad domain category for audit entries."""

    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"
    COMPLIANCE = "COMPLIANCE"
    OPERATIONAL = "OPERATIONAL"


class AuditStatus(StrEnum):
    """Lifecycle status of audit entries."""

    PERSISTED = "PERSISTED"
    ARCHIVED = "ARCHIVED"
    RETENTION_EXPIRED = "RETENTION_EXPIRED"


class MetricType(StrEnum):
    """Types of telemetry metrics."""

    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"
    TIMER = "TIMER"
    RATE = "RATE"


class ComponentStatus(StrEnum):
    """Health status of registered system components."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class SamplingStrategy(StrEnum):
    """Trace sampling algorithms."""

    ALWAYS_ON = "ALWAYS_ON"
    ALWAYS_OFF = "ALWAYS_OFF"
    PROBABILISTIC = "PROBABILISTIC"
    ERROR_ONLY = "ERROR_ONLY"
    CONFIGURABLE = "CONFIGURABLE"

