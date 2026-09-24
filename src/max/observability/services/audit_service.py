"""Append-only audit service for Module 33 — Observability & Audit."""

from datetime import datetime, timedelta
from typing import Any

from max.observability.domain.enums import (
    AuditActor,
    AuditCategory,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    AuditStatus,
)
from max.observability.domain.models import (
    AuditEvent,
    AuditEvidenceReference,
    AuditMetadata,
    generate_uuid,
    now_utc,
)
from max.observability.exporters.base import TelemetryExporter
from max.observability.repositories.interfaces import AuditEventRepository
from max.observability.services.correlation_service import CorrelationService
from max.observability.services.redaction_service import RedactionService


class AuditService:
    """Manages append-only security, system, and business audit records with durable accountability."""

    def __init__(
        self,
        repository: AuditEventRepository,
        exporter: TelemetryExporter | None = None,
        redaction_service: RedactionService | None = None,
        enabled: bool = True,
        default_retention_days: int = 90,
    ) -> None:
        self.repository = repository
        self.exporter = exporter
        self.redaction_service = redaction_service or RedactionService()
        self.enabled = enabled
        self.default_retention_days = default_retention_days

    async def record(
        self,
        event_type: AuditEventType,
        actor: AuditActor,
        action: str,
        target: str,
        actor_id: str = "system",
        target_id: str | None = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        severity: AuditSeverity = AuditSeverity.INFO,
        category: AuditCategory = AuditCategory.SYSTEM,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
        evidence: list[AuditEvidenceReference] | None = None,
        metadata: AuditMetadata | None = None,
        user_id: str | None = None,
        retention_days: int | None = None,
    ) -> AuditEvent:
        """Record an append-only audit event.

        Module 33 strictly records actions and security decisions (e.g. from Module 15),
        and DOES NOT alter or override authorization logic.
        """
        ctx = CorrelationService.get_current_context()

        # Sanitize details and reason to protect secrets
        clean_details = self.redaction_service.redact_dict(details or {})
        clean_reason = self.redaction_service.redact_text(reason) if reason else None

        days = retention_days if retention_days is not None else self.default_retention_days
        now_t = now_utc()
        retention_until = now_t + timedelta(days=days)

        event = AuditEvent(
            event_id=generate_uuid(),
            timestamp=now_t,
            event_type=event_type,
            actor=actor,
            actor_id=actor_id,
            target=target,
            target_id=target_id,
            action=action,
            outcome=outcome,
            severity=severity,
            category=category,
            reason=clean_reason,
            details=clean_details,
            evidence=evidence or [],
            metadata=metadata or AuditMetadata(),
            correlation_id=ctx.correlation_id,
            trace_id=ctx.trace_id,
            execution_id=ctx.execution_id,
            request_id=ctx.request_id,
            user_id=user_id or ctx.user_id,
            retention_days=days,
            retention_until=retention_until,
            status=AuditStatus.PERSISTED,
        )

        if self.enabled:
            await self.repository.append(event)
            if self.exporter:
                try:
                    await self.exporter.export_audit(event)
                except Exception:
                    pass

        return event

    async def get_event(self, event_id: str) -> AuditEvent | None:
        """Retrieve single audit event by ID."""
        return await self.repository.get_by_id(event_id)

    async def search_events(
        self,
        event_type: AuditEventType | None = None,
        actor: AuditActor | None = None,
        actor_id: str | None = None,
        target: str | None = None,
        outcome: AuditOutcome | None = None,
        severity: AuditSeverity | None = None,
        category: AuditCategory | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        execution_id: str | None = None,
        request_id: str | None = None,
        user_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Search immutable audit records."""
        return await self.repository.search(
            event_type=event_type,
            actor=actor,
            actor_id=actor_id,
            target=target,
            outcome=outcome,
            severity=severity,
            category=category,
            correlation_id=correlation_id,
            trace_id=trace_id,
            execution_id=execution_id,
            request_id=request_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )
