"""PolicyService for managing permission policy CRUD operations."""

from datetime import UTC, datetime
from typing import Any

from max.core.exceptions import NotFoundError
from max.security.domain.enums import PermissionScope, SecurityEventType
from max.security.domain.exceptions import InvalidPolicyError
from max.security.domain.permission import PermissionPolicy, PermissionRule
from max.security.repositories.policy_repository import BasePolicyRepository
from max.security.services.audit_service import SecurityAuditService


class PolicyService:
    """Service for permission policy management and lifecycle."""

    def __init__(
        self,
        policy_repository: BasePolicyRepository,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._policy_repo = policy_repository
        self._audit_service = audit_service

    def create_policy(
        self,
        name: str,
        owner_id: str,
        description: str | None = None,
        priority: int = 100,
        enabled: bool = True,
        rules: list[PermissionRule] | None = None,
        scope: PermissionScope = PermissionScope.GLOBAL,
    ) -> PermissionPolicy:
        """Create a new permission policy."""
        if not name or not name.strip():
            raise InvalidPolicyError("Policy name cannot be empty.")
        if not owner_id or not owner_id.strip():
            raise InvalidPolicyError("Policy owner_id cannot be empty.")

        policy = PermissionPolicy(
            name=name.strip(),
            description=description,
            priority=priority,
            enabled=enabled,
            rules=rules or [],
            scope=scope,
            owner_id=owner_id,
            version=1,
        )

        saved = self._policy_repo.save(policy)

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.POLICY_CHANGED,
                owner_id=owner_id,
                summary=f"Created policy '{policy.name}' (ID: {policy.policy_id})",
                metadata={"policy_id": policy.policy_id, "name": policy.name},
            )

        return saved

    def get_policy(self, policy_id: str) -> PermissionPolicy:
        """Retrieve policy by ID."""
        policy = self._policy_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Policy '{policy_id}' not found.")
        return policy

    def list_policies(
        self,
        owner_id: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionPolicy], int]:
        """List policies with filtering."""
        return self._policy_repo.list_policies(
            owner_id=owner_id,
            enabled_only=enabled_only,
            limit=limit,
            offset=offset,
        )

    def update_policy(
        self,
        policy_id: str,
        name: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        enabled: bool | None = None,
        rules: list[PermissionRule] | None = None,
    ) -> PermissionPolicy:
        """Update an existing policy."""
        existing = self.get_policy(policy_id)
        updates: dict[str, Any] = {"updated_at": datetime.now(UTC), "version": existing.version + 1}

        if name is not None:
            updates["name"] = name.strip()
        if description is not None:
            updates["description"] = description
        if priority is not None:
            updates["priority"] = priority
        if enabled is not None:
            updates["enabled"] = enabled
        if rules is not None:
            updates["rules"] = rules

        updated = existing.model_copy(update=updates)
        saved = self._policy_repo.save(updated)

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.POLICY_CHANGED,
                owner_id=existing.owner_id,
                summary=f"Updated policy '{existing.name}' to version {saved.version}",
                metadata={"policy_id": policy_id, "version": saved.version},
            )

        return saved

    def delete_policy(self, policy_id: str) -> bool:
        """Delete policy by ID."""
        existing = self.get_policy(policy_id)
        deleted = self._policy_repo.delete(policy_id)
        if deleted and self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.POLICY_CHANGED,
                owner_id=existing.owner_id,
                summary=f"Deleted policy '{existing.name}' (ID: {policy_id})",
                metadata={"policy_id": policy_id},
            )
        return deleted
