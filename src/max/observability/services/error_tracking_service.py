"""Structured error tracking and exception logging service for Module 33."""

from typing import Any

from max.observability.domain.enums import LogLevel
from max.observability.domain.models import ErrorRecord, generate_uuid, now_utc
from max.observability.repositories.interfaces import ErrorRepository
from max.observability.services.correlation_service import CorrelationService
from max.observability.services.metrics_service import MetricsService
from max.observability.services.redaction_service import RedactionService


class ErrorTrackingService:
    """Centralized exception handling integration and error tracking service."""

    def __init__(
        self,
        repository: ErrorRepository,
        metrics_service: MetricsService | None = None,
        redaction_service: RedactionService | None = None,
    ) -> None:
        self.repository = repository
        self.metrics_service = metrics_service
        self.redaction_service = redaction_service or RedactionService()

    async def record_exception(
        self,
        exception: Exception,
        component: str = "core",
        module: str = "module_33",
        operation: str = "unknown",
        retryable: bool = False,
        severity: LogLevel = LogLevel.ERROR,
        details: dict[str, Any] | None = None,
    ) -> ErrorRecord:
        """Record an exception with trace context, error metric increment, and safe error message."""
        ctx = CorrelationService.get_current_context()

        safe_msg = self.redaction_service.redact_text(str(exception))
        clean_details = self.redaction_service.redact_dict(details or {})

        error_rec = ErrorRecord(
            error_id=generate_uuid(),
            timestamp=now_utc(),
            error_type=type(exception).__name__,
            message_safe=safe_msg,
            component=component,
            module=module,
            operation=operation,
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
            request_id=ctx.request_id,
            execution_id=ctx.execution_id,
            stack_reference=f"err_{generate_uuid()[:8]}",
            retryable=retryable,
            severity=severity,
            details=clean_details,
        )

        await self.repository.record_error(error_rec)

        if self.metrics_service:
            await self.metrics_service.counter_increment(
                "errors_total",
                value=1.0,
                labels={
                    "module": module,
                    "component": component,
                    "error_type": error_rec.error_type,
                },
            )

        return error_rec

    async def get_errors(
        self,
        component: str | None = None,
        module: str | None = None,
        severity: LogLevel | None = None,
        trace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ErrorRecord]:
        """Query recorded error records."""
        return await self.repository.get_errors(
            component=component,
            module=module,
            severity=severity,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
        )
