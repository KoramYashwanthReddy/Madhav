"""Structured JSON logging service for Module 33 — Observability & Audit."""

import traceback
from typing import Any

from max.observability.domain.enums import LogLevel
from max.observability.domain.models import StructuredLogEntry, now_utc
from max.observability.exporters.base import TelemetryExporter
from max.observability.repositories.interfaces import LogRepository
from max.observability.services.correlation_service import CorrelationService
from max.observability.services.redaction_service import RedactionService

LEVEL_ORDER = {
    LogLevel.TRACE: 10,
    LogLevel.DEBUG: 20,
    LogLevel.INFO: 30,
    LogLevel.WARNING: 40,
    LogLevel.ERROR: 50,
    LogLevel.CRITICAL: 60,
}


class LoggingService:
    """Provides structured, trace-correlated, secret-redacted logging across system components."""

    def __init__(
        self,
        repository: LogRepository,
        exporter: TelemetryExporter | None = None,
        redaction_service: RedactionService | None = None,
        min_level: LogLevel = LogLevel.INFO,
        service_name: str = "max-ai",
        environment: str = "development",
        version: str = "1.0.0",
    ) -> None:
        self.repository = repository
        self.exporter = exporter
        self.redaction_service = redaction_service or RedactionService()
        self.min_level = min_level
        self.service_name = service_name
        self.environment = environment
        self.version = version

    def should_log(self, level: LogLevel) -> bool:
        """Determine if a log level satisfies the configured minimum severity."""
        return LEVEL_ORDER.get(level, 30) >= LEVEL_ORDER.get(self.min_level, 30)

    async def log(
        self,
        level: LogLevel,
        message: str,
        component: str = "core",
        module: str = "module_33",
        event_name: str = "system_event",
        attributes: dict[str, Any] | None = None,
        exception: Exception | None = None,
        user_id: str | None = None,
    ) -> StructuredLogEntry:
        """Create, sanitize, record, and export a structured log entry."""
        ctx = CorrelationService.get_current_context()

        # Sanitize message to prevent log injection and redact secrets
        clean_message = self.redaction_service.sanitize_log_message(message)

        # Redact attributes
        clean_attrs = self.redaction_service.redact_dict(attributes or {})

        exc_info = None
        if exception:
            exc_info = {
                "type": type(exception).__name__,
                "message": self.redaction_service.redact_text(str(exception)),
                "stack": traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                ),
            }

        entry = StructuredLogEntry(
            timestamp=now_utc(),
            level=level,
            message=clean_message,
            service=self.service_name,
            component=component,
            module=module,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
            execution_id=ctx.execution_id,
            user_id=user_id or ctx.user_id,
            event_name=event_name,
            attributes=clean_attrs,
            exception=exc_info,
            environment=self.environment,
            version=self.version,
        )

        if self.should_log(level):
            await self.repository.append(entry)
            if self.exporter:
                try:
                    await self.exporter.export_log(entry)
                except Exception:
                    pass  # Telemetry export failure should not break main execution flow

        return entry

    async def trace(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.TRACE, message, **kwargs)

    async def debug(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.DEBUG, message, **kwargs)

    async def info(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.INFO, message, **kwargs)

    async def warning(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.WARNING, message, **kwargs)

    async def error(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.ERROR, message, **kwargs)

    async def critical(self, message: str, **kwargs: Any) -> StructuredLogEntry:
        return await self.log(LogLevel.CRITICAL, message, **kwargs)
