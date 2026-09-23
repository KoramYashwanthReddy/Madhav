"""Domain exceptions for Module 14 Tool Registry."""

from typing import Any

from max.core.exceptions import MaxException


class ToolError(MaxException):
    """Base domain exception for all Tool Registry errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, code="TOOL_ERROR", details=details, status_code=400)


class ToolNotFoundError(ToolError):
    """Raised when a requested tool or version cannot be found."""

    def __init__(self, tool_identifier: str) -> None:
        super().__init__(f"Tool '{tool_identifier}' not found.")


class DuplicateToolError(ToolError):
    """Raised when registering a tool identity that already exists."""

    def __init__(self, tool_name: str, version: str) -> None:
        super().__init__(f"Tool '{tool_name}' version '{version}' is already registered.")


class InvalidToolDefinitionError(ToolError):
    """Raised when a tool definition fails structural validation rules."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid tool definition: {reason}")


class ToolVersionNotFoundError(ToolError):
    """Raised when a specific tool version is not found."""

    def __init__(self, tool_name: str, version: str) -> None:
        super().__init__(f"Tool '{tool_name}' version '{version}' not found.")


class ToolInactiveError(ToolError):
    """Raised when attempting an operation on a non-active tool."""

    def __init__(self, tool_id: str, current_status: str) -> None:
        super().__init__(f"Tool '{tool_id}' is not active (current status: '{current_status}').")


class ToolSchemaError(ToolError):
    """Raised when a tool input or output schema is malformed."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Tool schema error: {reason}")


class ToolArgumentValidationError(ToolError):
    """Raised when tool invocation arguments fail schema validation."""

    def __init__(self, tool_id: str, errors: list[str]) -> None:
        msg = f"Argument validation failed for tool '{tool_id}': {', '.join(errors)}"
        super().__init__(msg, details={"tool_id": tool_id, "errors": errors})


class ToolOutputValidationError(ToolError):
    """Raised when tool invocation output fails schema validation."""

    def __init__(self, tool_id: str, errors: list[str]) -> None:
        msg = f"Output validation failed for tool '{tool_id}': {', '.join(errors)}"
        super().__init__(msg, details={"tool_id": tool_id, "errors": errors})


class ToolInvocationNotFoundError(ToolError):
    """Raised when a requested tool invocation record is not found."""

    def __init__(self, invocation_id: str) -> None:
        super().__init__(f"Tool invocation '{invocation_id}' not found.")


class ToolInvocationStateError(ToolError):
    """Raised when an illegal transition on tool invocation state occurs."""

    def __init__(self, current_status: str, target_status: str) -> None:
        super().__init__(f"Invalid invocation transition from '{current_status}' to '{target_status}'.")


class ToolCapabilityError(ToolError):
    """Raised when a tool lacks required capabilities."""

    def __init__(self, tool_id: str, missing_capabilities: list[str]) -> None:
        msg = f"Tool '{tool_id}' missing required capabilities: {', '.join(missing_capabilities)}"
        super().__init__(msg, details={"tool_id": tool_id, "missing_capabilities": missing_capabilities})


class ToolPermissionRequiredError(ToolError):
    """Raised when invocation requires explicit permission approval from Module 15."""

    def __init__(self, tool_id: str, permission_name: str) -> None:
        msg = f"Invocation of tool '{tool_id}' requires permission '{permission_name}'."
        super().__init__(msg, details={"tool_id": tool_id, "permission_name": permission_name})


class ToolExecutionBoundaryError(ToolError):
    """Raised when an invocation reaches an un-implemented or restricted execution boundary."""

    def __init__(self, tool_id: str, boundary_reason: str) -> None:
        msg = f"Tool '{tool_id}' execution terminated at boundary: {boundary_reason}"
        super().__init__(msg, details={"tool_id": tool_id, "boundary_reason": boundary_reason})


class ToolTimeoutError(ToolError):
    """Raised when a tool invocation exceeds its maximum execution duration."""

    def __init__(self, invocation_id: str, timeout_seconds: float) -> None:
        msg = f"Tool invocation '{invocation_id}' timed out after {timeout_seconds} seconds."
        super().__init__(msg, details={"invocation_id": invocation_id, "timeout_seconds": timeout_seconds})
