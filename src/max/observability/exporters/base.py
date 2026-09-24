"""Base telemetry exporter interfaces for Module 33 — Observability & Audit."""

from abc import ABC, abstractmethod

from max.observability.domain.models import (
    AuditEvent,
    MetricValue,
    StructuredLogEntry,
    Trace,
)


class TelemetryExporter(ABC):
    """Abstract interface for exporting telemetry data (logs, traces, metrics, audit)."""

    @abstractmethod
    async def export_log(self, log_entry: StructuredLogEntry) -> bool:
        """Export a structured log entry."""
        pass

    @abstractmethod
    async def export_trace(self, trace: Trace) -> bool:
        """Export a trace."""
        pass

    @abstractmethod
    async def export_metric(self, metric: MetricValue) -> bool:
        """Export a metric value."""
        pass

    @abstractmethod
    async def export_audit(self, audit_event: AuditEvent) -> bool:
        """Export an audit event."""
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush pending buffered telemetry."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close exporter resources."""
        pass


class NoOpExporter(TelemetryExporter):
    """Exporter implementation that discards all telemetry data."""

    async def export_log(self, log_entry: StructuredLogEntry) -> bool:
        return True

    async def export_trace(self, trace: Trace) -> bool:
        return True

    async def export_metric(self, metric: MetricValue) -> bool:
        return True

    async def export_audit(self, audit_event: AuditEvent) -> bool:
        return True

    async def flush(self) -> None:
        pass

    async def close(self) -> None:
        pass
