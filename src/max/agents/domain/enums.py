"""Enumeration types for Module 13 Agent Engine."""

from enum import StrEnum


class AgentType(StrEnum):
    """Categorical classification of agent operational worker type."""

    GENERAL = "GENERAL"
    SPECIALIST = "SPECIALIST"
    COORDINATOR = "COORDINATOR"
    REVIEWER = "REVIEWER"
    PLANNER = "PLANNER"
    EXECUTOR = "EXECUTOR"


class AgentRole(StrEnum):
    """Functional responsibility role assigned to an agent."""

    ASSISTANT = "ASSISTANT"
    COORDINATOR = "COORDINATOR"
    RESEARCHER = "RESEARCHER"
    PLANNER = "PLANNER"
    CODER = "CODER"
    REVIEWER = "REVIEWER"
    ANALYST = "ANALYST"
    SYSTEM = "SYSTEM"


class AgentStatus(StrEnum):
    """Lifecycle state of an Agent definition."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ARCHIVED = "ARCHIVED"


class AgentCapability(StrEnum):
    """Capabilities an agent claims to handle (NOT permissions)."""

    PLANNING = "PLANNING"
    TASK_COORDINATION = "TASK_COORDINATION"
    RESEARCH = "RESEARCH"
    ANALYSIS = "ANALYSIS"
    CODE_REVIEW = "CODE_REVIEW"
    CONTENT_GENERATION = "CONTENT_GENERATION"
    DELEGATION = "DELEGATION"
    RESULT_REVIEW = "RESULT_REVIEW"


class AgentAssignmentStatus(StrEnum):
    """Lifecycle status of a task assignment to an agent."""

    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


AssignmentStatus = AgentAssignmentStatus


class AssignmentPriority(StrEnum):
    """Priority level for task assignment."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AgentRunStatus(StrEnum):
    """Lifecycle state of an AgentRun coordination instance."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class AgentExecutionMode(StrEnum):
    """Execution mode modes for agent coordination runs."""

    SYNCHRONOUS = "SYNCHRONOUS"
    ASYNCHRONOUS = "ASYNCHRONOUS"
    SUPERVISED = "SUPERVISED"
    DRY_RUN = "DRY_RUN"


class FailureCategory(StrEnum):
    """Taxonomy categories for agent run failures."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONTEXT_ERROR = "CONTEXT_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    TASK_ERROR = "TASK_ERROR"
    DELEGATION_ERROR = "DELEGATION_ERROR"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    TIMEOUT = "TIMEOUT"
    CANCELLATION = "CANCELLATION"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class NextAction(StrEnum):
    """Structured decision outcome indicating next step intent (NOT direct execution)."""

    COMPLETE = "COMPLETE"
    CONTINUE = "CONTINUE"
    WAIT = "WAIT"
    DELEGATE = "DELEGATE"
    REQUEST_TOOL = "REQUEST_TOOL"
    REQUEST_PERMISSION = "REQUEST_PERMISSION"
    FAIL = "FAIL"


class AgentEventType(StrEnum):
    """Operational trace event types (No private chain-of-thought)."""

    AGENT_CREATED = "AGENT_CREATED"
    AGENT_ACTIVATED = "AGENT_ACTIVATED"
    AGENT_PAUSED = "AGENT_PAUSED"
    AGENT_DISABLED = "AGENT_DISABLED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_ACCEPTED = "TASK_ACCEPTED"
    TASK_REJECTED = "TASK_REJECTED"
    RUN_CREATED = "RUN_CREATED"
    RUN_STARTED = "RUN_STARTED"
    RUN_WAITING = "RUN_WAITING"
    RUN_RESUMED = "RUN_RESUMED"
    RUN_COMPLETED = "RUN_COMPLETED"
    RUN_FAILED = "RUN_FAILED"
    RUN_CANCELLED = "RUN_CANCELLED"
    RUN_TIMED_OUT = "RUN_TIMED_OUT"
    DELEGATION_CREATED = "DELEGATION_CREATED"
    DELEGATION_COMPLETED = "DELEGATION_COMPLETED"
    DELEGATION_FAILED = "DELEGATION_FAILED"
    RESULT_CREATED = "RESULT_CREATED"


class DelegationStatus(StrEnum):
    """Lifecycle state of an inter-agent delegation link."""

    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RetryStrategy(StrEnum):
    """Backoff strategies for agent retry policies."""

    NONE = "NONE"
    FIXED = "FIXED"
    EXPONENTIAL = "EXPONENTIAL"
