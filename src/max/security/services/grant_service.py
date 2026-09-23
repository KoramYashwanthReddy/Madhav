"""PermissionGrantService for managing temporary and persistent permission grants."""

from datetime import UTC, datetime, timedelta

from max.core.exceptions import NotFoundError
from max.security.domain.enums import (
    PermissionAction,
    PermissionGrantType,
    PermissionScope,
    SecurityEventType,
)
from max.security.domain.exceptions import PermissionExpiredError
from max.security.domain.grant import PermissionGrant
from max.security.domain.resource import PermissionResource
from max.security.domain.subject import PermissionSubject
from max.security.repositories.permission_repository import BasePermissionGrantRepository
from max.security.services.audit_service import SecurityAuditService


class PermissionGrantService:
    """Service for issuing, querying, and revoking permission grants."""

    def __init__(
        self,
        grant_repository: BasePermissionGrantRepository,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._grant_repo = grant_repository
        self._audit_service = audit_service

    def create_grant(
        self,
        subject: PermissionSubject,
        action: PermissionAction,
        resource: PermissionResource,
        owner_id: str,
        grant_type: PermissionGrantType = PermissionGrantType.ONE_TIME,
        scope: PermissionScope = PermissionScope.EXACT_RESOURCE,
        duration_seconds: float | None = 3600.0,
    ) -> PermissionGrant:
        """Issue a new permission grant."""
        now = datetime.now(UTC)
        expires_at: datetime | None = None

        if grant_type in {
            PermissionGrantType.ONE_TIME,
            PermissionGrantType.TIME_LIMITED,
            PermissionGrantType.SESSION,
        }:
            if duration_seconds and duration_seconds > 0:
                expires_at = now + timedelta(seconds=duration_seconds)

        grant = PermissionGrant(
            subject=subject,
            action=action,
            resource=resource,
            scope=scope,
            grant_type=grant_type,
            owner_id=owner_id,
            created_at=now,
            expires_at=expires_at,
        )

        saved = self._grant_repo.save(grant)

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.PERMISSION_ALLOWED,
                owner_id=owner_id,
                summary=f"Issued permission grant '{saved.grant_id}' ({grant_type.value})",
                metadata={"grant_id": saved.grant_id, "grant_type": grant_type.value},
            )

        return saved

    def get_grant(self, grant_id: str) -> PermissionGrant:
        """Get grant by ID."""
        grant = self._grant_repo.get_by_id(grant_id)
        if not grant:
            raise NotFoundError(f"Permission grant '{grant_id}' not found.")
        return grant

    def list_grants(
        self,
        owner_id: str | None = None,
        subject_id: str | None = None,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PermissionGrant], int]:
        """List grants with filtering."""
        return self._grant_repo.list_grants(
            owner_id=owner_id,
            subject_id=subject_id,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )

    def revoke_grant(self, grant_id: str) -> PermissionGrant:
        """Revoke an active grant immediately."""
        grant = self.get_grant(grant_id)
        if not grant.is_active:
            raise PermissionExpiredError(f"Grant '{grant_id}' is already inactive or revoked.")

        revoked = self._grant_repo.revoke(grant_id)
        if not revoked:
            raise NotFoundError(f"Permission grant '{grant_id}' not found for revocation.")

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.PERMISSION_REVOKED,
                owner_id=grant.owner_id,
                summary=f"Revoked permission grant '{grant_id}'",
                metadata={"grant_id": grant_id},
            )

        return revoked
