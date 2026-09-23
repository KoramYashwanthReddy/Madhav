"""Services for recording security events and handling security violations."""

from typing import Any

from max.security.domain.audit import SecurityEvent, SecurityViolation
from max.security.domain.enums import PermissionAction, SecurityEventType, SecurityViolationType
from max.security.domain.subject import SecurityPrincipal
from max.security.repositories.audit_repository import (
    BaseSecurityEventRepository,
    BaseSecurityViolationRepository,
)


class SecurityAuditService:
    """Service for recording and querying immutable security audit events."""

    def __init__(self, event_repository: BaseSecurityEventRepository) -> None:
        self._event_repo = event_repository

    def record_event(
        self,
        event_type: SecurityEventType,
        owner_id: str,
        summary: str,
        principal: SecurityPrincipal | None = None,
        tool_id: str | None = None,
        action: PermissionAction | None = None,
        resource_id: str | None = None,
        request_id: str | None = None,
        decision_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Record an audit security event."""
        event = SecurityEvent(
            event_type=event_type,
            owner_id=owner_id,
            summary=summary,
            principal=principal,
            tool_id=tool_id,
            action=action,
            resource_id=resource_id,
            request_id=request_id,
            decision_id=decision_id,
            metadata=metadata or {},
        )
        return self._event_repo.record_event(event)

    def get_event(self, event_id: str) -> SecurityEvent | None:
        """Get event by ID."""
        return self._event_repo.get_by_id(event_id)

    def list_events(
        self,
        owner_id: str | None = None,
        event_type: SecurityEventType | None = None,
        request_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityEvent], int]:
        """List recorded audit events."""
        return self._event_repo.list_events(
            owner_id=owner_id,
            event_type=event_type,
            request_id=request_id,
            limit=limit,
            offset=offset,
        )


class SecurityViolationService:
    """Service for recording and investigating security violations."""

    def __init__(
        self,
        violation_repository: BaseSecurityViolationRepository,
        audit_service: SecurityAuditService | None = None,
    ) -> None:
        self._violation_repo = violation_repository
        self._audit_service = audit_service

    def record_violation(
        self,
        violation_type: SecurityViolationType,
        owner_id: str,
        summary: str,
        principal: SecurityPrincipal | None = None,
        tool_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> SecurityViolation:
        """Record a security boundary violation."""
        violation = SecurityViolation(
            violation_type=violation_type,
            owner_id=owner_id,
            summary=summary,
            principal=principal,
            tool_id=tool_id,
            details=details or {},
        )

        saved = self._violation_repo.record_violation(violation)

        if self._audit_service:
            self._audit_service.record_event(
                event_type=SecurityEventType.SECURITY_VIOLATION,
                owner_id=owner_id,
                summary=f"Security violation detected ({violation_type.value}): {summary}",
                principal=principal,
                tool_id=tool_id,
                metadata={"violation_id": saved.violation_id, "type": violation_type.value},
            )

        return saved

    def list_violations(
        self,
        owner_id: str | None = None,
        violation_type: SecurityViolationType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SecurityViolation], int]:
        """List recorded security violations."""
        return self._violation_repo.list_violations(
            owner_id=owner_id,
            violation_type=violation_type,
            limit=limit,
            offset=offset,
        )
