"""Repository interfaces and in-memory implementation for Permission Grants."""

import threading
from abc import ABC, abstractmethod
from datetime import UTC

from max.security.domain.grant import PermissionGrant


class BasePermissionGrantRepository(ABC):
    """Abstract repository for PermissionGrant persistence."""

    @abstractmethod
    def save(self, grant: PermissionGrant) -> PermissionGrant:
        """Save or update a permission grant."""
        pass

    @abstractmethod
    def get_by_id(self, grant_id: str) -> PermissionGrant | None:
        """Get grant by ID."""
        pass

    @abstractmethod
    def list_grants(
        self,
        owner_id: str | None = None,
        subject_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionGrant], int]:
        """List permission grants with filtering and pagination."""
        pass

    @abstractmethod
    def revoke(self, grant_id: str) -> PermissionGrant | None:
        """Revoke an active grant."""
        pass


class InMemoryPermissionGrantRepository(BasePermissionGrantRepository):
    """Thread-safe in-memory permission grant repository."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._grants: dict[str, PermissionGrant] = {}

    def save(self, grant: PermissionGrant) -> PermissionGrant:
        with self._lock:
            self._grants[grant.grant_id] = grant
            return grant

    def get_by_id(self, grant_id: str) -> PermissionGrant | None:
        with self._lock:
            return self._grants.get(grant_id)

    def list_grants(
        self,
        owner_id: str | None = None,
        subject_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionGrant], int]:
        with self._lock:
            filtered = list(self._grants.values())
            if owner_id is not None:
                filtered = [g for g in filtered if g.owner_id == owner_id]
            if subject_id is not None:
                filtered = [g for g in filtered if g.subject.subject_id == subject_id]
            if active_only:
                filtered = [g for g in filtered if g.is_active]

            filtered.sort(key=lambda g: g.created_at, reverse=True)
            total = len(filtered)
            paginated = filtered[offset : offset + limit]
            return paginated, total

    def revoke(self, grant_id: str) -> PermissionGrant | None:
        with self._lock:
            grant = self._grants.get(grant_id)
            if not grant:
                return None
            from datetime import datetime

            updated = grant.model_copy(update={"revoked_at": datetime.now(UTC)})
            self._grants[grant_id] = updated
            return updated
