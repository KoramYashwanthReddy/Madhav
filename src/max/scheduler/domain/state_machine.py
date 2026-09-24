"""Deterministic state machines for Schedule and Automation lifecycles."""

from max.scheduler.domain.enums import AutomationStatus, ScheduleStatus
from max.scheduler.domain.exceptions import InvalidStateTransitionError

VALID_SCHEDULE_TRANSITIONS: dict[ScheduleStatus, set[ScheduleStatus]] = {
    ScheduleStatus.DRAFT: {ScheduleStatus.SCHEDULED, ScheduleStatus.DISABLED},
    ScheduleStatus.SCHEDULED: {
        ScheduleStatus.READY,
        ScheduleStatus.PAUSED,
        ScheduleStatus.CANCELLED,
        ScheduleStatus.EXPIRED,
        ScheduleStatus.DISABLED,
    },
    ScheduleStatus.READY: {
        ScheduleStatus.RUNNING,
        ScheduleStatus.PAUSED,
        ScheduleStatus.CANCELLED,
        ScheduleStatus.DISABLED,
    },
    ScheduleStatus.RUNNING: {
        ScheduleStatus.COMPLETED,
        ScheduleStatus.FAILED,
        ScheduleStatus.PAUSED,
        ScheduleStatus.CANCELLED,
    },
    ScheduleStatus.PAUSED: {
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.READY,
        ScheduleStatus.CANCELLED,
        ScheduleStatus.DISABLED,
    },
    ScheduleStatus.FAILED: {
        ScheduleStatus.READY,
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.DISABLED,
    },
    ScheduleStatus.COMPLETED: {
        ScheduleStatus.READY,
        ScheduleStatus.SCHEDULED,
        ScheduleStatus.EXPIRED,
    },
    ScheduleStatus.CANCELLED: {ScheduleStatus.DRAFT, ScheduleStatus.SCHEDULED},
    ScheduleStatus.EXPIRED: {ScheduleStatus.DRAFT, ScheduleStatus.SCHEDULED},
    ScheduleStatus.DISABLED: {ScheduleStatus.DRAFT, ScheduleStatus.SCHEDULED},
}


VALID_AUTOMATION_TRANSITIONS: dict[AutomationStatus, set[AutomationStatus]] = {
    AutomationStatus.DRAFT: {AutomationStatus.SCHEDULED, AutomationStatus.DISABLED},
    AutomationStatus.SCHEDULED: {
        AutomationStatus.READY,
        AutomationStatus.PAUSED,
        AutomationStatus.CANCELLED,
        AutomationStatus.EXPIRED,
        AutomationStatus.DISABLED,
    },
    AutomationStatus.READY: {
        AutomationStatus.RUNNING,
        AutomationStatus.PAUSED,
        AutomationStatus.CANCELLED,
        AutomationStatus.DISABLED,
    },
    AutomationStatus.RUNNING: {
        AutomationStatus.COMPLETED,
        AutomationStatus.FAILED,
        AutomationStatus.PAUSED,
        AutomationStatus.CANCELLED,
    },
    AutomationStatus.PAUSED: {
        AutomationStatus.SCHEDULED,
        AutomationStatus.READY,
        AutomationStatus.CANCELLED,
        AutomationStatus.DISABLED,
    },
    AutomationStatus.FAILED: {
        AutomationStatus.READY,
        AutomationStatus.SCHEDULED,
        AutomationStatus.DISABLED,
    },
    AutomationStatus.COMPLETED: {
        AutomationStatus.READY,
        AutomationStatus.SCHEDULED,
        AutomationStatus.EXPIRED,
    },
    AutomationStatus.CANCELLED: {AutomationStatus.DRAFT, AutomationStatus.SCHEDULED},
    AutomationStatus.EXPIRED: {AutomationStatus.DRAFT, AutomationStatus.SCHEDULED},
    AutomationStatus.DISABLED: {AutomationStatus.DRAFT, AutomationStatus.SCHEDULED},
}


def validate_schedule_transition(
    current_status: ScheduleStatus, target_status: ScheduleStatus
) -> None:
    """Validate that transition from current_status to target_status is allowed.

    Raises InvalidStateTransitionError if transition is invalid.
    """
    if current_status == target_status:
        return

    allowed = VALID_SCHEDULE_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidStateTransitionError(
            current_state=current_status.value,
            target_state=target_status.value,
            entity_type="Schedule",
        )


def validate_automation_transition(
    current_status: AutomationStatus, target_status: AutomationStatus
) -> None:
    """Validate that transition from current_status to target_status is allowed.

    Raises InvalidStateTransitionError if transition is invalid.
    """
    if current_status == target_status:
        return

    allowed = VALID_AUTOMATION_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        raise InvalidStateTransitionError(
            current_state=current_status.value,
            target_state=target_status.value,
            entity_type="Automation",
        )
