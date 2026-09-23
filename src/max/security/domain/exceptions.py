"""Domain exceptions for Module 15 — Permission & Security."""

from typing import Any

from max.core.exceptions import MaxException


class SecurityError(MaxException):
    """Base exception for all security & permission errors."""

    def __init__(
        self,
        message: str = "A security policy enforcement error occurred.",
        code: str = "SECURITY_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class PermissionDeniedError(SecurityError):
    """Action request was explicitly or implicitly denied by security policy."""

    def __init__(
        self,
        message: str = "Permission denied for requested action.",
        code: str = "PERMISSION_DENIED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class PermissionRequiredError(SecurityError):
    """Action request requires explicit user approval before execution."""

    def __init__(
        self,
        message: str = "Requested action requires explicit user approval.",
        code: str = "APPROVAL_REQUIRED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 402,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class PermissionExpiredError(SecurityError):
    """Permission decision or grant has expired."""

    def __init__(
        self,
        message: str = "Permission grant or decision has expired.",
        code: str = "PERMISSION_EXPIRED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class EmergencyBlockError(SecurityError):
    """Emergency block or kill switch is active."""

    def __init__(
        self,
        message: str = "Emergency block is active. Action blocked.",
        code: str = "EMERGENCY_BLOCK_ACTIVE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 423,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SecurityModeError(SecurityError):
    """Security mode restricts the requested action."""

    def __init__(
        self,
        message: str = "Current security mode restricts this action.",
        code: str = "SECURITY_MODE_RESTRICTED",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SecurityViolationError(SecurityError):
    """Security boundary or policy integrity violation detected."""

    def __init__(
        self,
        message: str = "Security boundary violation detected.",
        code: str = "SECURITY_VIOLATION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 403,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SecurityContextError(SecurityError):
    """Security context is malformed, incomplete, or invalid."""

    def __init__(
        self,
        message: str = "Security context is invalid or incomplete.",
        code: str = "INVALID_SECURITY_CONTEXT",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class SecurityEvaluationError(SecurityError):
    """Internal failure occurred during policy evaluation (fails closed)."""

    def __init__(
        self,
        message: str = "Policy evaluation failed unexpectedly.",
        code: str = "EVALUATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidPolicyError(SecurityError):
    """Policy definition is invalid."""

    def __init__(
        self,
        message: str = "Permission policy definition is invalid.",
        code: str = "INVALID_POLICY",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ApprovalNotFoundError(SecurityError):
    """Approval request not found."""

    def __init__(
        self,
        message: str = "Approval request not found.",
        code: str = "APPROVAL_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidApprovalError(SecurityError):
    """Approval request operation is invalid or state is finalized."""

    def __init__(
        self,
        message: str = "Invalid approval request operation.",
        code: str = "INVALID_APPROVAL",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
