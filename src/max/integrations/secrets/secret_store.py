"""SecretStore abstraction and in-memory development implementation for Module 29."""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Any

from max.integrations.domain.exceptions import SecretStoreError

logger = logging.getLogger(__name__)


class SecretStore(ABC):
    """Abstract interface for secure secret storage backends.

    CRITICAL SECURITY BOUNDARY:
    Raw secrets (tokens, keys, passwords) MUST remain inside SecretStore
    and never leak into domain objects, loggers, exceptions, or API endpoints.
    """

    @abstractmethod
    def store(self, secret_id: str, secret_data: dict[str, Any]) -> str:
        """Store secret payload securely and return secret_id key."""
        pass

    @abstractmethod
    def retrieve(self, secret_id: str) -> dict[str, Any]:
        """Retrieve raw secret payload by secret_id key."""
        pass

    @abstractmethod
    def delete(self, secret_id: str) -> bool:
        """Delete secret payload by secret_id key."""
        pass

    @abstractmethod
    def rotate(self, secret_id: str, new_secret_data: dict[str, Any]) -> None:
        """Rotate secret payload under existing secret_id key."""
        pass

    @abstractmethod
    def exists(self, secret_id: str) -> bool:
        """Check if secret_id key exists in store."""
        pass


class InMemorySecretStore(SecretStore):
    """Thread-safe in-memory SecretStore for development and testing.

    Ensures secrets are kept isolated and strings/reprs mask content.
    """

    def __init__(self) -> None:
        self._secrets: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def __repr__(self) -> str:
        return f"<InMemorySecretStore count={len(self._secrets)} [REDACTED]>"

    def __str__(self) -> str:
        return self.__repr__()

    def store(self, secret_id: str, secret_data: dict[str, Any]) -> str:
        with self._lock:
            if not secret_id:
                raise SecretStoreError("secret_id", "Secret ID cannot be empty.")
            # Store deep copy of dictionary
            self._secrets[secret_id] = dict(secret_data)
            logger.debug("Stored secret under key '%s'", secret_id)
            return secret_id

    def retrieve(self, secret_id: str) -> dict[str, Any]:
        with self._lock:
            if secret_id not in self._secrets:
                raise SecretStoreError(secret_id, f"Secret '{secret_id}' not found in SecretStore.")
            return dict(self._secrets[secret_id])

    def delete(self, secret_id: str) -> bool:
        with self._lock:
            if secret_id in self._secrets:
                del self._secrets[secret_id]
                logger.debug("Deleted secret under key '%s'", secret_id)
                return True
            return False

    def rotate(self, secret_id: str, new_secret_data: dict[str, Any]) -> None:
        with self._lock:
            if secret_id not in self._secrets:
                raise SecretStoreError(secret_id, f"Cannot rotate non-existent secret '{secret_id}'.")
            self._secrets[secret_id] = dict(new_secret_data)
            logger.debug("Rotated secret under key '%s'", secret_id)

    def exists(self, secret_id: str) -> bool:
        with self._lock:
            return secret_id in self._secrets
