"""Domain enumerations for Module 23 — Developer Agent."""

from enum import Enum


class DevSessionStatus(str, Enum):
    """Lifecycle states for a DeveloperSession."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


class WorkflowType(str, Enum):
    """High-level categories of developer workflows."""

    FEATURE = "FEATURE"
    BUGFIX = "BUGFIX"
    RELEASE = "RELEASE"
    HOTFIX = "HOTFIX"
    REFACTOR = "REFACTOR"
    CUSTOM = "CUSTOM"


class WorkflowStatus(str, Enum):
    """State machine statuses for a DeveloperWorkflow."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class WorkflowStep(str, Enum):
    """Ordered steps within a developer workflow."""

    INIT = "INIT"
    CREATE_BRANCH = "CREATE_BRANCH"
    DELEGATE_CODING = "DELEGATE_CODING"
    STAGE_AND_COMMIT = "STAGE_AND_COMMIT"
    PUSH = "PUSH"
    OPEN_PR = "OPEN_PR"
    AWAIT_REVIEW = "AWAIT_REVIEW"
    MERGE = "MERGE"
    TAG_RELEASE = "TAG_RELEASE"
    CLEANUP = "CLEANUP"
    DONE = "DONE"


class PRStatus(str, Enum):
    """Pull request lifecycle states."""

    DRAFT = "DRAFT"
    OPEN = "OPEN"
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    MERGED = "MERGED"
    CLOSED = "CLOSED"


class IssueStatus(str, Enum):
    """Issue tracker item states."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    WONT_FIX = "WONT_FIX"


class IssuePriority(str, Enum):
    """Priority levels for issues."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CIRunStatus(str, Enum):
    """CI/CD pipeline run states."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class MergeStrategy(str, Enum):
    """Strategies for merging branches."""

    MERGE_COMMIT = "MERGE_COMMIT"
    SQUASH = "SQUASH"
    REBASE = "REBASE"


class GitOperationRisk(str, Enum):
    """Risk classification for Git operations."""

    READ_ONLY = "READ_ONLY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
