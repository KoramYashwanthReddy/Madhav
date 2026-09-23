"""Enumeration types for Module 12 Task Engine."""

from enum import StrEnum


class TaskType(StrEnum):
    """Controlled categories of tasks."""

    GENERAL = "GENERAL"
    RESEARCH = "RESEARCH"
    ANALYSIS = "ANALYSIS"
    CODING = "CODING"
    WRITING = "WRITING"
    REVIEW = "REVIEW"
    PLANNING = "PLANNING"
    MAINTENANCE = "MAINTENANCE"
    PERSONAL = "PERSONAL"
    SYSTEM = "SYSTEM"
    OTHER = "OTHER"


class TaskStatus(StrEnum):
    """Lifecycle execution statuses for tasks."""

    PENDING = "PENDING"
    READY = "READY"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    SKIPPED = "SKIPPED"


class TaskPriority(StrEnum):
    """Controlled priority levels for tasks."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        """Numeric rank for deterministic sorting (higher is more urgent)."""
        ranks = {
            TaskPriority.LOW: 0,
            TaskPriority.NORMAL: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.URGENT: 3,
            TaskPriority.CRITICAL: 4,
        }
        return ranks[self]


class TaskSource(StrEnum):
    """Origin categories describing where a task came from."""

    USER = "USER"
    CONVERSATION = "CONVERSATION"
    PLAN = "PLAN"
    REASONING = "REASONING"
    SYSTEM = "SYSTEM"
    IMPORTED = "IMPORTED"
    MANUAL = "MANUAL"
    FUTURE_AGENT = "FUTURE_AGENT"


class DependencyType(StrEnum):
    """Relationship categories between tasks."""

    BLOCKS = "BLOCKS"
    DEPENDS_ON = "DEPENDS_ON"
    RELATED_TO = "RELATED_TO"


class RecurrenceType(StrEnum):
    """Controlled schedule recurrence patterns (metadata abstraction)."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    CUSTOM = "CUSTOM"


class TaskReferenceType(StrEnum):
    """Categories of referenced artifacts linked to a task."""

    PLAN = "PLAN"
    PLAN_STEP = "PLAN_STEP"
    REASONING = "REASONING"
    CONVERSATION = "CONVERSATION"
    MEMORY = "MEMORY"
    KNOWLEDGE = "KNOWLEDGE"
    DOCUMENT = "DOCUMENT"


class TaskReadinessStatus(StrEnum):
    """Calculated readiness states for tasks."""

    READY = "READY"
    BLOCKED = "BLOCKED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    INVALID = "INVALID"


class TaskGroupStatus(StrEnum):
    """Status categories for task groups."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    COMPLETED = "COMPLETED"
