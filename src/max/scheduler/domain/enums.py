"""Domain enums for Module 28 — Scheduler & Automation Engine."""

from enum import StrEnum


class ScheduleType(StrEnum):
    """Supported schedule execution types."""

    ONE_TIME = "ONE_TIME"
    RECURRING = "RECURRING"
    CRON = "CRON"
    INTERVAL = "INTERVAL"
    EVENT = "EVENT"
    CONDITIONAL = "CONDITIONAL"


class ScheduleStatus(StrEnum):
    """Lifecycle status states for schedules."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class AutomationStatus(StrEnum):
    """Lifecycle status states for automations."""

    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class TriggerType(StrEnum):
    """Supported trigger types."""

    TIME_TRIGGER = "TIME_TRIGGER"
    INTERVAL_TRIGGER = "INTERVAL_TRIGGER"
    CRON_TRIGGER = "CRON_TRIGGER"
    EVENT_TRIGGER = "EVENT_TRIGGER"
    CONDITION_TRIGGER = "CONDITION_TRIGGER"
    MANUAL_TRIGGER = "MANUAL_TRIGGER"


class TriggerStatus(StrEnum):
    """Status of triggers."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"


class MisfirePolicy(StrEnum):
    """Policy when a schedule missed its execution time."""

    SKIP = "SKIP"
    RUN_ONCE = "RUN_ONCE"
    RUN_IMMEDIATELY = "RUN_IMMEDIATELY"
    CATCH_UP = "CATCH_UP"


class ConcurrencyPolicy(StrEnum):
    """Policy handling concurrent executions of the same job."""

    ALLOW = "ALLOW"
    FORBID = "FORBID"
    REPLACE = "REPLACE"
    QUEUE = "QUEUE"


class BackoffStrategy(StrEnum):
    """Retry backoff strategies."""

    FIXED_BACKOFF = "FIXED_BACKOFF"
    EXPONENTIAL_BACKOFF = "EXPONENTIAL_BACKOFF"


class ConditionOperator(StrEnum):
    """Operators for structured conditional automation evaluation."""

    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    LESS_EQUAL = "LESS_EQUAL"
    CONTAINS = "CONTAINS"
    IN = "IN"
    MATCHES_REGEX = "MATCHES_REGEX"


class StepType(StrEnum):
    """Types of steps in an automation workflow."""

    CREATE_TASK = "CREATE_TASK"
    WAIT = "WAIT"
    CHECK_CONDITION = "CHECK_CONDITION"
    ASSIGN_AGENT = "ASSIGN_AGENT"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    VERIFY_RESULT = "VERIFY_RESULT"
    SEND_NOTIFICATION = "SEND_NOTIFICATION"


class ExecutionStatus(StrEnum):
    """Status of automation executions."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"


class SchedulerAuditEventType(StrEnum):
    """Auditable events produced by the scheduler."""

    SCHEDULE_CREATED = "SCHEDULE_CREATED"
    SCHEDULE_UPDATED = "SCHEDULE_UPDATED"
    SCHEDULE_PAUSED = "SCHEDULE_PAUSED"
    SCHEDULE_RESUMED = "SCHEDULE_RESUMED"
    SCHEDULE_CANCELLED = "SCHEDULE_CANCELLED"
    SCHEDULE_TRIGGERED = "SCHEDULE_TRIGGERED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTION_RETRIED = "EXECUTION_RETRIED"
    EXECUTION_SKIPPED = "EXECUTION_SKIPPED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    EXECUTION_DENIED = "EXECUTION_DENIED"
    LOCK_ACQUIRED = "LOCK_ACQUIRED"
    LOCK_RELEASED = "LOCK_RELEASED"
