"""Domain exceptions for Module 28 — Scheduler & Automation Engine."""

from typing import Any


class SchedulerError(Exception):
    """Base exception for all scheduler and automation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ScheduleNotFoundError(SchedulerError):
    """Raised when a requested schedule cannot be found."""

    def __init__(self, schedule_id: str) -> None:
        super().__init__(f"Schedule '{schedule_id}' not found.", {"schedule_id": schedule_id})


class AutomationNotFoundError(SchedulerError):
    """Raised when a requested automation cannot be found."""

    def __init__(self, automation_id: str) -> None:
        super().__init__(f"Automation '{automation_id}' not found.", {"automation_id": automation_id})


class ExecutionNotFoundError(SchedulerError):
    """Raised when a requested execution record cannot be found."""

    def __init__(self, execution_id: str) -> None:
        super().__init__(f"Execution '{execution_id}' not found.", {"execution_id": execution_id})


class InvalidStateTransitionError(SchedulerError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_state: str, target_state: str, entity_type: str = "Schedule") -> None:
        super().__init__(
            f"Invalid {entity_type} state transition from '{current_state}' to '{target_state}'.",
            {"current_state": current_state, "target_state": target_state, "entity_type": entity_type},
        )


class ScheduleValidationError(SchedulerError):
    """Raised when schedule parameters or definitions fail validation."""

    pass


class AutomationValidationError(SchedulerError):
    """Raised when automation parameters or definitions fail validation."""

    pass


class CircularDependencyError(SchedulerError):
    """Raised when circular dependencies between automations are detected."""

    pass


class LockAcquisitionError(SchedulerError):
    """Raised when a scheduler lock cannot be acquired."""

    pass


class RateLimitExceededError(SchedulerError):
    """Raised when automation execution rate limits are exceeded."""

    pass


class PermissionDeniedError(SchedulerError):
    """Raised when Module 15 denies permission for an automation action."""

    pass


class ExecutionCancelledError(SchedulerError):
    """Raised when an in-flight execution is explicitly cancelled."""

    pass
