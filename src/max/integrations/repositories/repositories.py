"""Repository abstractions and thread-safe memory implementations for Module 29."""

import builtins
import threading
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from max.integrations.domain.models import (
    Integration,
    IntegrationAuditEvent,
    IntegrationConnection,
    IntegrationProvider,
    WebhookEvent,
    WebhookSubscription,
)


class BaseIntegrationRepository(ABC):
    @abstractmethod
    def save(self, integration: Integration) -> Integration:
        pass

    @abstractmethod
    def get_by_id(self, integration_id: str) -> Integration | None:
        pass

    @abstractmethod
    def get_by_key(self, integration_key: str) -> Integration | None:
        pass

    @abstractmethod
    def list(self, category: str | None = None, limit: int = 100, offset: int = 0) -> builtins.list[Integration]:
        pass


class BaseProviderRepository(ABC):
    @abstractmethod
    def save(self, provider: IntegrationProvider) -> IntegrationProvider:
        pass

    @abstractmethod
    def get_by_key(self, provider_key: str) -> IntegrationProvider | None:
        pass

    @abstractmethod
    def list(self) -> builtins.list[IntegrationProvider]:
        pass


class BaseConnectionRepository(ABC):
    @abstractmethod
    def save(self, connection: IntegrationConnection) -> IntegrationConnection:
        pass

    @abstractmethod
    def get_by_id(self, connection_id: str) -> IntegrationConnection | None:
        pass

    @abstractmethod
    def list_by_owner(
        self, owner_id: str, integration_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> builtins.list[IntegrationConnection]:
        pass

    @abstractmethod
    def delete(self, connection_id: str) -> bool:
        pass


class BaseWebhookSubscriptionRepository(ABC):
    @abstractmethod
    def save(self, subscription: WebhookSubscription) -> WebhookSubscription:
        pass

    @abstractmethod
    def get_by_id(self, subscription_id: str) -> WebhookSubscription | None:
        pass

    @abstractmethod
    def list_by_integration(self, integration_id: str) -> builtins.list[WebhookSubscription]:
        pass

    @abstractmethod
    def delete(self, subscription_id: str) -> bool:
        pass


class BaseWebhookEventRepository(ABC):
    @abstractmethod
    def save(self, event: WebhookEvent) -> WebhookEvent:
        pass

    @abstractmethod
    def get_by_id(self, event_id: str) -> WebhookEvent | None:
        pass

    @abstractmethod
    def exists_by_signature(self, signature_ref: str) -> bool:
        pass


class BaseIntegrationAuditRepository(ABC):
    @abstractmethod
    def save(self, event: IntegrationAuditEvent) -> IntegrationAuditEvent:
        pass

    @abstractmethod
    def list_by_owner(
        self, owner_id: str, limit: int = 100, offset: int = 0
    ) -> builtins.list[IntegrationAuditEvent]:
        pass


# =========================================================
# In-Memory Implementations
# =========================================================


class MemoryIntegrationRepository(BaseIntegrationRepository):
    def __init__(self) -> None:
        self._integrations: dict[str, Integration] = {}
        self._key_map: dict[str, str] = {}
        self._lock = threading.RLock()

    def save(self, integration: Integration) -> Integration:
        with self._lock:
            copied = integration.model_copy(deep=True)
            self._integrations[copied.integration_id] = copied
            self._key_map[copied.integration_key] = copied.integration_id
            return copied.model_copy(deep=True)

    def get_by_id(self, integration_id: str) -> Integration | None:
        with self._lock:
            item = self._integrations.get(integration_id)
            return item.model_copy(deep=True) if item else None

    def get_by_key(self, integration_key: str) -> Integration | None:
        with self._lock:
            iid = self._key_map.get(integration_key)
            if not iid:
                return None
            item = self._integrations.get(iid)
            return item.model_copy(deep=True) if item else None

    def list(self, category: str | None = None, limit: int = 100, offset: int = 0) -> builtins.list[Integration]:
        with self._lock:
            results = builtins.list(self._integrations.values())
            if category:
                results = [i for i in results if i.category.value == category or i.category == category]
            return [i.model_copy(deep=True) for i in results[offset : offset + limit]]


class MemoryProviderRepository(BaseProviderRepository):
    def __init__(self) -> None:
        self._providers: dict[str, IntegrationProvider] = {}
        self._lock = threading.RLock()

    def save(self, provider: IntegrationProvider) -> IntegrationProvider:
        with self._lock:
            copied = provider.model_copy(deep=True)
            self._providers[copied.provider_key] = copied
            return copied.model_copy(deep=True)

    def get_by_key(self, provider_key: str) -> IntegrationProvider | None:
        with self._lock:
            item = self._providers.get(provider_key)
            return item.model_copy(deep=True) if item else None

    def list(self) -> builtins.list[IntegrationProvider]:
        with self._lock:
            return [p.model_copy(deep=True) for p in self._providers.values()]


class MemoryConnectionRepository(BaseConnectionRepository):
    def __init__(self) -> None:
        self._connections: dict[str, IntegrationConnection] = {}
        self._lock = threading.RLock()

    def save(self, connection: IntegrationConnection) -> IntegrationConnection:
        with self._lock:
            copied = connection.model_copy(deep=True)
            copied.updated_at = datetime.now(UTC)
            self._connections[copied.connection_id] = copied
            return copied.model_copy(deep=True)

    def get_by_id(self, connection_id: str) -> IntegrationConnection | None:
        with self._lock:
            item = self._connections.get(connection_id)
            return item.model_copy(deep=True) if item else None

    def list_by_owner(
        self, owner_id: str, integration_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> builtins.list[IntegrationConnection]:
        with self._lock:
            results = [c for c in self._connections.values() if c.owner_id == owner_id]
            if integration_id:
                results = [c for c in results if c.integration_id == integration_id]
            return [c.model_copy(deep=True) for c in results[offset : offset + limit]]

    def delete(self, connection_id: str) -> bool:
        with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
                return True
            return False


class MemoryWebhookSubscriptionRepository(BaseWebhookSubscriptionRepository):
    def __init__(self) -> None:
        self._subscriptions: dict[str, WebhookSubscription] = {}
        self._lock = threading.RLock()

    def save(self, subscription: WebhookSubscription) -> WebhookSubscription:
        with self._lock:
            copied = subscription.model_copy(deep=True)
            self._subscriptions[copied.subscription_id] = copied
            return copied.model_copy(deep=True)

    def get_by_id(self, subscription_id: str) -> WebhookSubscription | None:
        with self._lock:
            item = self._subscriptions.get(subscription_id)
            return item.model_copy(deep=True) if item else None

    def list_by_integration(self, integration_id: str) -> builtins.list[WebhookSubscription]:
        with self._lock:
            return [
                s.model_copy(deep=True) for s in self._subscriptions.values() if s.integration_id == integration_id
            ]

    def delete(self, subscription_id: str) -> bool:
        with self._lock:
            if subscription_id in self._subscriptions:
                del self._subscriptions[subscription_id]
                return True
            return False


class MemoryWebhookEventRepository(BaseWebhookEventRepository):
    def __init__(self) -> None:
        self._events: dict[str, WebhookEvent] = {}
        self._signatures: set[str] = set()
        self._lock = threading.RLock()

    def save(self, event: WebhookEvent) -> WebhookEvent:
        with self._lock:
            copied = event.model_copy(deep=True)
            self._events[copied.event_id] = copied
            if copied.payload_reference:
                self._signatures.add(copied.payload_reference)
            return copied.model_copy(deep=True)

    def get_by_id(self, event_id: str) -> WebhookEvent | None:
        with self._lock:
            item = self._events.get(event_id)
            return item.model_copy(deep=True) if item else None

    def exists_by_signature(self, signature_ref: str) -> bool:
        with self._lock:
            return signature_ref in self._signatures


class MemoryIntegrationAuditRepository(BaseIntegrationAuditRepository):
    def __init__(self) -> None:
        self._events: builtins.list[IntegrationAuditEvent] = []
        self._lock = threading.RLock()

    def save(self, event: IntegrationAuditEvent) -> IntegrationAuditEvent:
        with self._lock:
            copied = event.model_copy(deep=True)
            self._events.append(copied)
            return copied.model_copy(deep=True)

    def list_by_owner(
        self, owner_id: str, limit: int = 100, offset: int = 0
    ) -> builtins.list[IntegrationAuditEvent]:
        with self._lock:
            results = [e for e in self._events if e.owner_id == owner_id or owner_id == "system"]
            return [e.model_copy(deep=True) for e in results[offset : offset + limit]]
