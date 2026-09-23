"""Repository interfaces and in-memory implementation for Permission Policies."""

import threading
from abc import ABC, abstractmethod

from max.security.domain.permission import PermissionPolicy


class BasePolicyRepository(ABC):
    """Abstract repository interface for PermissionPolicy management."""

    @abstractmethod
    def save(self, policy: PermissionPolicy) -> PermissionPolicy:
        """Save or update a permission policy."""
        pass

    @abstractmethod
    def get_by_id(self, policy_id: str) -> PermissionPolicy | None:
        """Get policy by ID."""
        pass

    @abstractmethod
    def list_policies(
        self,
        owner_id: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionPolicy], int]:
        """List permission policies with filtering and pagination."""
        pass

    @abstractmethod
    def delete(self, policy_id: str) -> bool:
        """Delete policy by ID."""
        pass


class InMemoryPolicyRepository(BasePolicyRepository):
    """Thread-safe in-memory policy repository implementation."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._policies: dict[str, PermissionPolicy] = {}

    def save(self, policy: PermissionPolicy) -> PermissionPolicy:
        with self._lock:
            self._policies[policy.policy_id] = policy
            return policy

    def get_by_id(self, policy_id: str) -> PermissionPolicy | None:
        with self._lock:
            return self._policies.get(policy_id)

    def list_policies(
        self,
        owner_id: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionPolicy], int]:
        with self._lock:
            filtered = list(self._policies.values())
            if owner_id is not None:
                filtered = [p for p in filtered if p.owner_id == owner_id]
            if enabled_only:
                filtered = [p for p in filtered if p.enabled]

            # Sort by priority descending then created_at
            filtered.sort(key=lambda p: (p.priority, p.created_at), reverse=True)

            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total

    def delete(self, policy_id: str) -> bool:
        with self._lock:
            if policy_id in self._policies:
                del self._policies[policy_id]
                return True
            return False
