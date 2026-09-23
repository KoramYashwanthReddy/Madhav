"""Model Management subsystem custom exceptions."""

from typing import Any

from max.core.exceptions import MaxException


class ModelManagementError(MaxException):
    """Base exception for Model Management subsystem errors."""

    def __init__(
        self,
        message: str = "A model management error occurred.",
        code: str = "MODEL_MANAGEMENT_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelNotFoundError(ModelManagementError):
    """Raised when a requested model is not found in the repository."""

    def __init__(
        self,
        message: str = "The specified model was not found.",
        code: str = "MODEL_NOT_FOUND",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 404,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelAlreadyExistsError(ModelManagementError):
    """Raised when registering a model ID that is already registered."""

    def __init__(
        self,
        message: str = "A model with the specified identifier already exists.",
        code: str = "MODEL_ALREADY_EXISTS",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 409,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelValidationError(ModelManagementError):
    """Raised when model metadata or path configuration fails validation."""

    def __init__(
        self,
        message: str = "Model validation failed.",
        code: str = "MODEL_VALIDATION_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelLoadError(ModelManagementError):
    """Raised when a model fails to load into runtime."""

    def __init__(
        self,
        message: str = "Failed to load model into runtime.",
        code: str = "MODEL_LOAD_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelUnloadError(ModelManagementError):
    """Raised when unloading a model fails."""

    def __init__(
        self,
        message: str = "Failed to unload model from runtime.",
        code: str = "MODEL_UNLOAD_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelUnavailableError(ModelManagementError):
    """Raised when attempting an operation on an unavailable model."""

    def __init__(
        self,
        message: str = "The specified model is currently unavailable.",
        code: str = "MODEL_UNAVAILABLE",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 503,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelCompatibilityError(ModelManagementError):
    """Raised when model capabilities are incompatible with target runtime."""

    def __init__(
        self,
        message: str = "Model capabilities are incompatible with target runtime.",
        code: str = "MODEL_COMPATIBILITY_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class ModelIntegrityError(ModelManagementError):
    """Raised when model artifact checksum verification fails."""

    def __init__(
        self,
        message: str = "Model artifact integrity check failed.",
        code: str = "MODEL_INTEGRITY_ERROR",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)


class InvalidModelStateTransitionError(ModelManagementError):
    """Raised when attempting an illegal lifecycle state transition."""

    def __init__(
        self,
        message: str = "Invalid model lifecycle state transition attempted.",
        code: str = "INVALID_MODEL_STATE_TRANSITION",
        details: dict[str, Any] | list[Any] | None = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message=message, code=code, details=details, status_code=status_code)
