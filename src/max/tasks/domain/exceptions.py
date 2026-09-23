"""Domain exceptions for Module 12 Task Engine."""

from typing import Any

from max.core.exceptions import MaxException


class TaskError(MaxException):
    """Base exception for Task Engine subsystem."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="TASK_ERROR", details=details)


class TaskNotFoundError(TaskError):
    """Raised when a requested task record is not found."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Task record with ID '{task_id}' was not found.",
            details={"task_id": task_id},
        )


class TaskValidationError(TaskError):
    """Raised when task parameters or metadata validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class InvalidTaskStateTransitionError(TaskError):
    """Raised when an invalid task status transition is attempted."""

    def __init__(self, current_status: str, target_status: str, reason: str | None = None) -> None:
        msg = f"Invalid state transition from '{current_status}' to '{target_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            msg,
            details={
                "current_status": current_status,
                "target_status": target_status,
                "reason": reason,
            },
        )


class TaskDependencyError(TaskError):
    """Raised when task dependency operations or references are invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class CircularTaskDependencyError(TaskDependencyError):
    """Raised when a circular dependency loop is detected in the task dependency graph."""

    def __init__(self, cycle: list[str]) -> None:
        cycle_str = " -> ".join(cycle)
        super().__init__(
            f"Circular task dependency detected: {cycle_str}",
            details={"cycle": cycle},
        )


class TaskHierarchyError(TaskError):
    """Raised when parent-child task nesting hierarchy is invalid or circular."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class TaskOwnershipError(TaskError):
    """Raised when an operation violates task ownership boundaries."""

    def __init__(self, task_id: str, owner_id: str, requesting_owner_id: str) -> None:
        super().__init__(
            f"Task '{task_id}' owned by '{owner_id}' cannot be accessed by '{requesting_owner_id}'.",
            details={
                "task_id": task_id,
                "owner_id": owner_id,
                "requesting_owner_id": requesting_owner_id,
            },
        )


class TaskGroupNotFoundError(TaskError):
    """Raised when requested task group is not found."""

    def __init__(self, group_id: str) -> None:
        super().__init__(
            f"Task group record with ID '{group_id}' was not found.",
            details={"group_id": group_id},
        )


class TaskGroupOwnershipError(TaskError):
    """Raised when task group ownership boundary is violated."""

    def __init__(self, group_id: str, owner_id: str, requesting_owner_id: str) -> None:
        super().__init__(
            f"Task group '{group_id}' owned by '{owner_id}' cannot be accessed by '{requesting_owner_id}'.",
            details={
                "group_id": group_id,
                "owner_id": owner_id,
                "requesting_owner_id": requesting_owner_id,
            },
        )


class InvalidTaskProgressError(TaskError):
    """Raised when progress percentage is outside valid 0-100 range or inconsistent."""

    def __init__(self, progress: int, reason: str | None = None) -> None:
        msg = f"Invalid progress value '{progress}'. Must be between 0 and 100."
        if reason:
            msg += f" {reason}"
        super().__init__(msg, details={"progress": progress, "reason": reason})


class TaskAlreadyCompletedError(TaskError):
    """Raised when attempting an operation invalid for a completed task."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Task '{task_id}' is already completed.",
            details={"task_id": task_id},
        )


class TaskCancelledError(TaskError):
    """Raised when attempting an operation invalid for a cancelled task."""

    def __init__(self, task_id: str) -> None:
        super().__init__(
            f"Task '{task_id}' has been cancelled.",
            details={"task_id": task_id},
        )


class TaskRetryNotAllowedError(TaskError):
    """Raised when retrying a task is not allowed due to state or retry policy limits."""

    def __init__(self, task_id: str, reason: str) -> None:
        super().__init__(
            f"Cannot retry task '{task_id}': {reason}",
            details={"task_id": task_id, "reason": reason},
        )


class PlanTaskGenerationError(TaskError):
    """Raised when generating tasks from a reasoning plan fails."""

    def __init__(self, plan_id: str, reason: str) -> None:
        super().__init__(
            f"Failed to generate tasks for plan '{plan_id}': {reason}",
            details={"plan_id": plan_id, "reason": reason},
        )
