"""Domain exceptions for Module 29 — External Integrations."""

from typing import Any


class IntegrationError(Exception):
    """Base exception for all integration module errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProviderNotFoundError(IntegrationError):
    """Raised when an integration provider key is not registered."""

    def __init__(self, provider_key: str) -> None:
        super().__init__(
            f"Integration provider '{provider_key}' is not registered.",
            details={"provider_key": provider_key},
        )


class IntegrationNotFoundError(IntegrationError):
    """Raised when an integration ID is not found."""

    def __init__(self, integration_id: str) -> None:
        super().__init__(
            f"Integration '{integration_id}' was not found.",
            details={"integration_id": integration_id},
        )


class ConnectionNotFoundError(IntegrationError):
    """Raised when a connection ID is not found."""

    def __init__(self, connection_id: str) -> None:
        super().__init__(
            f"Integration connection '{connection_id}' was not found.",
            details={"connection_id": connection_id},
        )


class AuthenticationFailedError(IntegrationError):
    """Raised when authentication or token refresh fails."""

    def __init__(self, provider_key: str, reason: str) -> None:
        super().__init__(
            f"Authentication failed for provider '{provider_key}': {reason}",
            details={"provider_key": provider_key, "reason": reason},
        )


class PermissionDeniedIntegrationError(IntegrationError):
    """Raised when Module 15 denies permission for an integration action."""

    def __init__(self, action_id: str, reason: str) -> None:
        super().__init__(
            f"Permission denied for integration action '{action_id}': {reason}",
            details={"action_id": action_id, "reason": reason},
        )


class RateLimitExceededError(IntegrationError):
    """Raised when connection or provider rate limit ceiling is reached."""

    def __init__(self, connection_id: str, retry_after_seconds: float = 60.0) -> None:
        super().__init__(
            f"Rate limit exceeded for connection '{connection_id}'. Retry after {retry_after_seconds}s.",
            details={"connection_id": connection_id, "retry_after_seconds": retry_after_seconds},
        )


class InvalidWebhookSignatureError(IntegrationError):
    """Raised when webhook signature verification fails."""

    def __init__(self, integration_id: str, reason: str = "Invalid signature") -> None:
        super().__init__(
            f"Webhook signature validation failed for integration '{integration_id}': {reason}",
            details={"integration_id": integration_id, "reason": reason},
        )


class SecretStoreError(IntegrationError):
    """Raised when secret storage operations fail."""

    def __init__(self, secret_id: str, reason: str) -> None:
        super().__init__(
            f"SecretStore operation failed for secret '{secret_id}': {reason}",
            details={"secret_id": secret_id, "reason": reason},
        )


class ActionExecutionError(IntegrationError):
    """Raised when action execution encounters an unrecoverable error."""

    def __init__(self, action_id: str, error_code: str, message: str) -> None:
        super().__init__(
            f"Action '{action_id}' failed ({error_code}): {message}",
            details={"action_id": action_id, "error_code": error_code, "message": message},
        )


class OAuthStateValidationError(IntegrationError):
    """Raised when OAuth state token is invalid, expired, or mismatched."""

    def __init__(self, reason: str = "State mismatch or expired") -> None:
        super().__init__(
            f"OAuth2 state validation failed: {reason}",
            details={"reason": reason},
        )
