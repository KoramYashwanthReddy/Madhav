"""Domain exceptions for Reasoning & Planning Engine."""

from typing import Any

from max.core.exceptions import MaxException


class ReasoningError(MaxException):
    """Base exception for Reasoning & Planning subsystem."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="REASONING_ERROR", details=details)


class ReasoningRequestValidationError(ReasoningError):
    """Raised when reasoning request payload validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class ReasoningNotFoundError(ReasoningError):
    """Raised when requested reasoning request or result is not found."""

    def __init__(self, reasoning_id: str) -> None:
        super().__init__(
            f"Reasoning record with ID '{reasoning_id}' was not found.",
            details={"reasoning_id": reasoning_id},
        )


class PlanNotFoundError(ReasoningError):
    """Raised when requested plan is not found."""

    def __init__(self, plan_id: str) -> None:
        super().__init__(
            f"Plan record with ID '{plan_id}' was not found.",
            details={"plan_id": plan_id},
        )


class PlanValidationError(ReasoningError):
    """Raised when plan structural validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class PlanDependencyError(ReasoningError):
    """Raised when plan step dependencies are invalid or missing."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class CircularDependencyError(ReasoningError):
    """Raised when a circular dependency loop is detected in plan steps."""

    def __init__(self, cycle: list[str]) -> None:
        cycle_str = " -> ".join(cycle)
        super().__init__(
            f"Circular dependency detected in plan steps: {cycle_str}.",
            details={"cycle": cycle},
        )


class InvalidPlanStateError(ReasoningError):
    """Raised when an invalid plan transition or step status is requested."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class ReasoningProviderError(ReasoningError):
    """Raised when reasoning provider computation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class MalformedReasoningOutputError(ReasoningError):
    """Raised when AI model output fails schema validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class ReasoningContextError(ReasoningError):
    """Raised when context preparation or budget allocation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=details)


class OwnershipError(ReasoningError):
    """Raised when owner isolation boundary is violated."""

    def __init__(
        self,
        message: str = "Access denied: Owner mismatch.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)

