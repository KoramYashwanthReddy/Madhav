"""Domain enums for Reasoning & Planning Engine."""

from enum import StrEnum


class ReasoningMode(StrEnum):
    """Supported cognitive reasoning modes."""

    ANALYSIS = "ANALYSIS"
    PLANNING = "PLANNING"
    DECISION_SUPPORT = "DECISION_SUPPORT"
    PROBLEM_SOLVING = "PROBLEM_SOLVING"
    DECOMPOSITION = "DECOMPOSITION"
    SUMMARIZATION = "SUMMARIZATION"
    EVALUATION = "EVALUATION"


class ReasoningStatus(StrEnum):
    """Reasoning request execution lifecycle state."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


class PlanStatus(StrEnum):
    """Plan lifecycle status."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    SUPERSEDED = "SUPERSEDED"
    INVALID = "INVALID"


class PlanStepStatus(StrEnum):
    """State of an individual plan step."""

    PENDING = "PENDING"
    READY = "READY"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class ConstraintClassification(StrEnum):
    """Hard vs soft constraint priority boundary."""

    HARD = "HARD"
    SOFT = "SOFT"


class ConfidenceLevel(StrEnum):
    """Subjective evidence-based confidence classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ComplexityLevel(StrEnum):
    """Estimated planning step complexity."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(StrEnum):
    """Estimated risk classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CompletenessStatus(StrEnum):
    """Plan structural completeness validation evaluation."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"


class ConstraintType(StrEnum):
    """Categories of constraints."""

    TECHNOLOGY = "technology"
    TIME = "time"
    BUDGET = "budget"
    ENVIRONMENT = "environment"
    PREFERENCE = "preference"
    SYSTEM = "system"

