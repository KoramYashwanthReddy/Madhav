"""Domain models, value objects, enums, and exceptions for Task Engine."""

from max.tasks.domain.dependency import TaskDependency
from max.tasks.domain.enums import (
    DependencyType,
    RecurrenceType,
    TaskGroupStatus,
    TaskPriority,
    TaskReadinessStatus,
    TaskReferenceType,
    TaskSource,
    TaskStatus,
    TaskType,
)
from max.tasks.domain.exceptions import (
    CircularTaskDependencyError,
    InvalidTaskProgressError,
    InvalidTaskStateTransitionError,
    PlanTaskGenerationError,
    TaskAlreadyCompletedError,
    TaskCancelledError,
    TaskDependencyError,
    TaskError,
    TaskGroupNotFoundError,
    TaskGroupOwnershipError,
    TaskHierarchyError,
    TaskNotFoundError,
    TaskOwnershipError,
    TaskRetryNotAllowedError,
    TaskValidationError,
)
from max.tasks.domain.group import TaskGroup, TaskGroupSummary
from max.tasks.domain.history import TaskHistoryEntry
from max.tasks.domain.references import TaskReference
from max.tasks.domain.schedule import TaskRecurrence, TaskSchedule
from max.tasks.domain.task import Task, TaskFailure, TaskResult, TaskSummary

__all__ = [
    "TaskType",
    "TaskStatus",
    "TaskPriority",
    "TaskSource",
    "DependencyType",
    "RecurrenceType",
    "TaskReferenceType",
    "TaskReadinessStatus",
    "TaskGroupStatus",
    "TaskError",
    "TaskNotFoundError",
    "TaskValidationError",
    "InvalidTaskStateTransitionError",
    "TaskDependencyError",
    "CircularTaskDependencyError",
    "TaskHierarchyError",
    "TaskOwnershipError",
    "TaskGroupNotFoundError",
    "TaskGroupOwnershipError",
    "InvalidTaskProgressError",
    "TaskAlreadyCompletedError",
    "TaskCancelledError",
    "TaskRetryNotAllowedError",
    "PlanTaskGenerationError",
    "Task",
    "TaskResult",
    "TaskFailure",
    "TaskSummary",
    "TaskDependency",
    "TaskGroup",
    "TaskGroupSummary",
    "TaskHistoryEntry",
    "TaskReference",
    "TaskSchedule",
    "TaskRecurrence",
]
