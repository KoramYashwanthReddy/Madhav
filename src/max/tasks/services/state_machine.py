"""Task lifecycle state machine implementation."""

from max.tasks.domain.enums import TaskStatus
from max.tasks.domain.exceptions import InvalidTaskStateTransitionError


class TaskStateMachine:
    """Validates lifecycle state transitions for tasks."""

    VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {
            TaskStatus.READY,
            TaskStatus.BLOCKED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.PAUSED,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.READY: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.PAUSED,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.BLOCKED: {
            TaskStatus.READY,
            TaskStatus.PENDING,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.IN_PROGRESS: {
            TaskStatus.PAUSED,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.PAUSED: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.FAILED: {
            TaskStatus.READY,  # Retry/reset state transition
            TaskStatus.CANCELLED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.COMPLETED: set(),  # Terminal state
        TaskStatus.CANCELLED: set(),  # Terminal state
        TaskStatus.EXPIRED: set(),  # Terminal state
        TaskStatus.SKIPPED: set(),  # Terminal state
    }

    @classmethod
    def can_transition(cls, current_status: TaskStatus, target_status: TaskStatus) -> bool:
        """Check if transition from current_status to target_status is valid."""
        if current_status == target_status:
            return True
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def validate_transition(
        cls, current_status: TaskStatus, target_status: TaskStatus, reason: str | None = None
    ) -> None:
        """Validate state transition or raise InvalidTaskStateTransitionError."""
        if current_status == target_status:
            return
        if not cls.can_transition(current_status, target_status):
            raise InvalidTaskStateTransitionError(
                current_status=current_status.value,
                target_status=target_status.value,
                reason=reason,
            )
