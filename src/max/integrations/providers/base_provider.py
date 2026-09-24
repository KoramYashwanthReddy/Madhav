"""Provider interface for Module 29 — External Integrations."""

from abc import ABC, abstractmethod
from typing import Any

from max.integrations.domain.enums import ErrorCode, IntegrationCategory
from max.integrations.domain.models import (
    CredentialReference,
    ExternalEvent,
    IntegrationCapability,
    IntegrationConnection,
    IntegrationErrorModel,
    IntegrationResponse,
    WebhookSubscription,
)
from max.integrations.secrets.secret_store import SecretStore


class ExternalIntegrationProvider(ABC):
    """Abstract Base Class for provider-neutral external service adapters."""

    @property
    @abstractmethod
    def provider_key(self) -> str:
        """Unique provider key (e.g. mock_email, github, google_calendar)."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of the provider."""
        pass

    @property
    @abstractmethod
    def category(self) -> IntegrationCategory:
        """Primary category of the provider."""
        pass

    @abstractmethod
    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        """Establish account connection and store raw credentials in SecretStore."""
        pass

    @abstractmethod
    def disconnect(self, connection: IntegrationConnection, secret_store: SecretStore) -> bool:
        """Disconnect account and delete credentials from SecretStore."""
        pass

    @abstractmethod
    def authenticate(self, connection: IntegrationConnection, secret_store: SecretStore) -> bool:
        """Verify connection credentials against provider."""
        pass

    @abstractmethod
    def refresh_credentials(
        self, connection: IntegrationConnection, secret_store: SecretStore
    ) -> IntegrationConnection:
        """Refresh expired credentials (e.g. OAuth2 refresh token flow)."""
        pass

    @abstractmethod
    def health_check(self, connection: IntegrationConnection, secret_store: SecretStore) -> dict[str, Any]:
        """Perform health check on connection status and latency."""
        pass

    @abstractmethod
    def list_capabilities(self) -> list[IntegrationCapability]:
        """Return list of supported integration capabilities."""
        pass

    @abstractmethod
    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        """Execute a structured action against external service."""
        pass

    @abstractmethod
    def subscribe_webhook(
        self,
        connection: IntegrationConnection | None,
        event_type: str,
        endpoint: str,
        secret_store: SecretStore,
    ) -> WebhookSubscription:
        """Register a webhook subscription with provider."""
        pass

    @abstractmethod
    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        """Cancel a webhook subscription with provider."""
        pass

    @abstractmethod
    def handle_webhook(
        self,
        headers: dict[str, str],
        payload: dict[str, Any] | str,
        subscription: WebhookSubscription,
        secret_store: SecretStore,
    ) -> ExternalEvent:
        """Validate signature, sanitize, and normalize webhook payload into ExternalEvent."""
        pass

    def normalize_error(self, error: Exception) -> IntegrationErrorModel:
        """Normalize exceptions into provider-neutral error model."""
        return IntegrationErrorModel(
            error_code=ErrorCode.UNKNOWN,
            category="GENERAL",
            message=str(error),
            retryable=False,
        )
