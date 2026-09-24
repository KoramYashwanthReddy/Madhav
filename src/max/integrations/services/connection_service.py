"""Connection Service managing external account connection lifecycles for Module 29."""

import logging
from typing import Any

from max.integrations.adapters.adapters import Module27NotificationAdapter
from max.integrations.domain.enums import ConnectionStatus
from max.integrations.domain.exceptions import ConnectionNotFoundError
from max.integrations.domain.models import IntegrationConnection
from max.integrations.repositories.repositories import (
    BaseConnectionRepository,
    MemoryConnectionRepository,
)
from max.integrations.secrets.secret_store import SecretStore
from max.integrations.services.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class ConnectionService:
    """Manages integration account connections, credential attachment, health checks, and lifecycle states."""

    def __init__(
        self,
        registry: IntegrationRegistry,
        secret_store: SecretStore,
        connection_repo: BaseConnectionRepository | None = None,
        notification_adapter: Module27NotificationAdapter | None = None,
    ) -> None:
        self._registry = registry
        self._secret_store = secret_store
        self._connection_repo = connection_repo or MemoryConnectionRepository()
        self._notification_adapter = notification_adapter or Module27NotificationAdapter()

    def connect_account(
        self, provider_key: str, owner_id: str, auth_data: dict[str, Any]
    ) -> IntegrationConnection:
        """Establish account connection with provider and store credentials safely."""
        provider = self._registry.get_provider(provider_key)
        conn, cred_ref = provider.connect(owner_id, auth_data, self._secret_store)

        saved = self._connection_repo.save(conn)

        self._notification_adapter.notify(
            owner_id=owner_id,
            title="Integration Connected",
            body=f"Successfully connected account to '{provider.name}'.",
        )
        logger.info("Connected account for owner '%s' to provider '%s'", owner_id, provider_key)
        return saved

    def get_connection(self, connection_id: str) -> IntegrationConnection:
        """Retrieve connection by ID."""
        conn = self._connection_repo.get_by_id(connection_id)
        if not conn:
            raise ConnectionNotFoundError(connection_id)
        return conn

    def list_connections(
        self, owner_id: str, integration_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[IntegrationConnection]:
        """List connections for an owner user."""
        return self._connection_repo.list_by_owner(owner_id, integration_id=integration_id, limit=limit, offset=offset)

    def health_check(self, connection_id: str) -> dict[str, Any]:
        """Perform health check on a connection."""
        conn = self.get_connection(connection_id)
        provider = self._registry.get_provider(conn.credential_ref.provider_key if conn.credential_ref else "mock")
        res = provider.health_check(conn, self._secret_store)
        self._connection_repo.save(conn)
        return res

    def refresh_connection(self, connection_id: str) -> IntegrationConnection:
        """Refresh expired credentials for a connection."""
        conn = self.get_connection(connection_id)
        provider = self._registry.get_provider(conn.credential_ref.provider_key if conn.credential_ref else "mock")
        refreshed = provider.refresh_credentials(conn, self._secret_store)
        saved = self._connection_repo.save(refreshed)

        self._notification_adapter.notify(
            owner_id=conn.owner_id,
            title="Integration Refreshed",
            body=f"Credentials refreshed for connection '{connection_id}'.",
        )
        return saved

    def disconnect_account(self, connection_id: str) -> bool:
        """Disconnect account and delete credentials."""
        conn = self.get_connection(connection_id)
        provider = self._registry.get_provider(conn.credential_ref.provider_key if conn.credential_ref else "mock")
        provider.disconnect(conn, self._secret_store)
        self._connection_repo.save(conn)

        self._notification_adapter.notify(
            owner_id=conn.owner_id,
            title="Integration Disconnected",
            body=f"Connection '{connection_id}' has been disconnected.",
        )
        return True

    def revoke_connection(self, connection_id: str) -> bool:
        """Revoke connection immediately."""
        conn = self.get_connection(connection_id)
        if conn.credential_ref:
            self._secret_store.delete(conn.credential_ref.credential_id)
        conn.status = ConnectionStatus.REVOKED
        self._connection_repo.save(conn)

        self._notification_adapter.notify(
            owner_id=conn.owner_id,
            title="Integration Revoked",
            body=f"Connection '{connection_id}' was revoked.",
        )
        return True
