"""Domain exceptions for Module 13 Agent Engine."""

from typing import Any

from max.core.exceptions import MaxException


class AgentError(MaxException):
    """Base exception for Agent Engine subsystem."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="AGENT_ERROR", details=details)


class AgentNotFoundError(AgentError):
    """Raised when a requested Agent record is not found."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(
            f"Agent with ID '{agent_id}' was not found.",
            details={"agent_id": agent_id},
        )


class AgentInactiveError(AgentError):
    """Raised when operating on an inactive, disabled, or archived agent."""

    def __init__(self, agent_id: str, status: str) -> None:
        super().__init__(
            f"Agent '{agent_id}' is not active (current status: '{status}').",
            details={"agent_id": agent_id, "status": status},
        )


class AgentCapabilityMismatchError(AgentError):
    """Raised when an agent lacks required capabilities for an assigned task."""

    def __init__(self, agent_id: str, missing_capabilities: list[str]) -> None:
        super().__init__(
            f"Agent '{agent_id}' lacks required capabilities: {', '.join(missing_capabilities)}",
            details={"agent_id": agent_id, "missing_capabilities": missing_capabilities},
        )


class AgentAssignmentNotFoundError(AgentError):
    """Raised when an AgentAssignment record is not found."""

    def __init__(self, assignment_id: str) -> None:
        super().__init__(
            f"Agent assignment '{assignment_id}' was not found.",
            details={"assignment_id": assignment_id},
        )


class AgentRunNotFoundError(AgentError):
    """Raised when an AgentRun instance is not found."""

    def __init__(self, run_id: str) -> None:
        super().__init__(
            f"Agent run '{run_id}' was not found.",
            details={"run_id": run_id},
        )


class InvalidAgentStateTransitionError(AgentError):
    """Raised when an invalid Agent definition status transition is attempted."""

    def __init__(self, current_status: str, target_status: str, reason: str | None = None) -> None:
        msg = f"Invalid agent state transition from '{current_status}' to '{target_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            msg,
            details={"current_status": current_status, "target_status": target_status, "reason": reason},
        )


class InvalidRunStateTransitionError(AgentError):
    """Raised when an invalid AgentRun status transition is attempted."""

    def __init__(self, current_status: str, target_status: str, reason: str | None = None) -> None:
        msg = f"Invalid agent run state transition from '{current_status}' to '{target_status}'."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(
            msg,
            details={"current_status": current_status, "target_status": target_status, "reason": reason},
        )


class AgentLimitExceededError(AgentError):
    """Raised when an agent limit (max tasks, max steps, max depth) is exceeded."""

    def __init__(self, limit_name: str, current_val: int, max_val: int) -> None:
        super().__init__(
            f"Agent limit '{limit_name}' exceeded ({current_val} > {max_val}).",
            details={"limit_name": limit_name, "current_val": current_val, "max_val": max_val},
        )


class DelegationCycleError(AgentError):
    """Raised when circular inter-agent delegation is detected."""

    def __init__(self, cycle: list[str]) -> None:
        cycle_str = " -> ".join(cycle)
        super().__init__(
            f"Circular agent delegation detected: {cycle_str}",
            details={"cycle": cycle},
        )


class DelegationLimitExceededError(AgentError):
    """Raised when delegation count or nesting depth exceeds configured limits."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class AgentUnavailableError(AgentError):
    """Raised when no suitable or available agent can be selected."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"No available agent found: {reason}", details={"reason": reason})


class AgentExecutionBoundaryError(AgentError):
    """Raised when attempting tool/action execution beyond Module 13 boundary."""

    def __init__(self, boundary_name: str, message: str) -> None:
        super().__init__(
            f"Execution boundary hit ({boundary_name}): {message}",
            details={"boundary_name": boundary_name, "message": message},
        )
