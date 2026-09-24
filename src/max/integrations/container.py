"""Dependency Injection Container for Module 29 — External Integrations."""

import logging
import threading

from max.integrations.auth.oauth2 import OAuth2Handler
from max.integrations.providers.mock_providers import (
    MockCalendarProvider,
    MockEmailProvider,
    MockGitHubProvider,
    MockStorageProvider,
    MockWebhookProvider,
)
from max.integrations.secrets.secret_store import InMemorySecretStore, SecretStore
from max.integrations.services.connection_service import ConnectionService
from max.integrations.services.execution_service import IntegrationExecutionService
from max.integrations.services.registry import IntegrationRegistry
from max.integrations.webhooks.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class IntegrationContainer:
    """Dependency injection container holding Integration singletons."""

    def __init__(self) -> None:
        self.secret_store: SecretStore = InMemorySecretStore()
        self.registry: IntegrationRegistry = IntegrationRegistry()
        self.oauth2_handler: OAuth2Handler = OAuth2Handler()
        self.connection_service: ConnectionService = ConnectionService(
            registry=self.registry,
            secret_store=self.secret_store,
        )
        self.execution_service: IntegrationExecutionService = IntegrationExecutionService(
            registry=self.registry,
            connection_service=self.connection_service,
            secret_store=self.secret_store,
        )
        self.webhook_service: WebhookService = WebhookService(
            registry=self.registry,
            secret_store=self.secret_store,
        )
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Auto-register deterministic mock integration providers."""
        mocks = [
            MockEmailProvider(),
            MockCalendarProvider(),
            MockStorageProvider(),
            MockGitHubProvider(),
            MockWebhookProvider(),
        ]
        for p in mocks:
            try:
                self.registry.register_provider(p)
            except Exception as exc:
                logger.warning("Failed to register mock provider '%s': %s", p.provider_key, exc)


_container_instance: IntegrationContainer | None = None
_container_lock = threading.RLock()


def get_integration_container() -> IntegrationContainer:
    """Retrieve or initialize global IntegrationContainer singleton."""
    global _container_instance
    with _container_lock:
        if _container_instance is None:
            _container_instance = IntegrationContainer()
        return _container_instance


def reset_integration_container() -> None:
    """Reset global IntegrationContainer singleton instance (primarily for test isolation)."""
    global _container_instance
    with _container_lock:
        _container_instance = None
