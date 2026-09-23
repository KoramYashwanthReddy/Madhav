"""State machine services for Agent definition lifecycle and AgentRun execution lifecycle."""

from max.agents.domain.enums import AgentRunStatus, AgentStatus
from max.agents.domain.exceptions import (
    InvalidAgentStateTransitionError,
    InvalidRunStateTransitionError,
)


class AgentStateMachine:
    """Validates lifecycle status transitions for Agent definitions."""

    VALID_TRANSITIONS: dict[AgentStatus, set[AgentStatus]] = {
        AgentStatus.CREATED: {AgentStatus.ACTIVE, AgentStatus.DISABLED},
        AgentStatus.ACTIVE: {AgentStatus.PAUSED, AgentStatus.DISABLED, AgentStatus.ARCHIVED},
        AgentStatus.PAUSED: {AgentStatus.ACTIVE, AgentStatus.DISABLED},
        AgentStatus.DISABLED: {AgentStatus.ACTIVE, AgentStatus.ARCHIVED},
        AgentStatus.ARCHIVED: set(),  # Terminal
    }

    @classmethod
    def can_transition(cls, current_status: AgentStatus, target_status: AgentStatus) -> bool:
        if current_status == target_status:
            return True
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def validate_transition(
        cls, current_status: AgentStatus, target_status: AgentStatus, reason: str | None = None
    ) -> None:
        if current_status == target_status:
            return
        if not cls.can_transition(current_status, target_status):
            raise InvalidAgentStateTransitionError(
                current_status=current_status.value,
                target_status=target_status.value,
                reason=reason,
            )

    @classmethod
    def validate_agent_transition(
        cls, current_status: AgentStatus, target_status: AgentStatus, reason: str | None = None
    ) -> None:
        cls.validate_transition(current_status, target_status, reason)

    @classmethod
    def can_transition_run(cls, current_status: AgentRunStatus, target_status: AgentRunStatus) -> bool:
        return AgentRunStateMachine.can_transition(current_status, target_status)

    @classmethod
    def validate_run_transition(
        cls, current_status: AgentRunStatus, target_status: AgentRunStatus, reason: str | None = None
    ) -> None:
        AgentRunStateMachine.validate_transition(current_status, target_status, reason)


class AgentRunStateMachine:
    """Validates lifecycle status transitions for AgentRun execution instances."""

    VALID_TRANSITIONS: dict[AgentRunStatus, set[AgentRunStatus]] = {
        AgentRunStatus.CREATED: {AgentRunStatus.INITIALIZING, AgentRunStatus.CANCELLED},
        AgentRunStatus.INITIALIZING: {
            AgentRunStatus.READY,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
        },
        AgentRunStatus.READY: {AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED},
        AgentRunStatus.RUNNING: {
            AgentRunStatus.WAITING,
            AgentRunStatus.PAUSED,
            AgentRunStatus.COMPLETED,
            AgentRunStatus.FAILED,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.TIMED_OUT,
        },
        AgentRunStatus.WAITING: {
            AgentRunStatus.RUNNING,
            AgentRunStatus.CANCELLED,
            AgentRunStatus.FAILED,
            AgentRunStatus.TIMED_OUT,
        },
        AgentRunStatus.PAUSED: {AgentRunStatus.RUNNING, AgentRunStatus.CANCELLED},
        AgentRunStatus.FAILED: {AgentRunStatus.READY, AgentRunStatus.CANCELLED},  # Retry
        AgentRunStatus.COMPLETED: set(),  # Terminal
        AgentRunStatus.CANCELLED: set(),  # Terminal
        AgentRunStatus.TIMED_OUT: set(),  # Terminal
    }

    @classmethod
    def can_transition(cls, current_status: AgentRunStatus, target_status: AgentRunStatus) -> bool:
        if current_status == target_status:
            return True
        allowed = cls.VALID_TRANSITIONS.get(current_status, set())
        return target_status in allowed

    @classmethod
    def validate_transition(
        cls, current_status: AgentRunStatus, target_status: AgentRunStatus, reason: str | None = None
    ) -> None:
        if current_status == target_status:
            return
        if not cls.can_transition(current_status, target_status):
            raise InvalidRunStateTransitionError(
                current_status=current_status.value,
                target_status=target_status.value,
                reason=reason,
            )
