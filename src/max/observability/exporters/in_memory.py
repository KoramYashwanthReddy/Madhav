"""In-memory telemetry exporter for testing and local development."""

import asyncio

from max.observability.domain.models import (
    AuditEvent,
    MetricValue,
    StructuredLogEntry,
    Trace,
)
from max.observability.exporters.base import TelemetryExporter


class InMemoryExporter(TelemetryExporter):
    """Accumulates exported telemetry items in memory for inspection during tests."""

    def __init__(self) -> None:
        self.exported_logs: list[StructuredLogEntry] = []
        self.exported_traces: list[Trace] = []
        self.exported_metrics: list[MetricValue] = []
        self.exported_audits: list[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def export_log(self, log_entry: StructuredLogEntry) -> bool:
        async with self._lock:
            self.exported_logs.append(log_entry)
        return True

    async def export_trace(self, trace: Trace) -> bool:
        async with self._lock:
            self.exported_traces.append(trace)
        return True

    async def export_metric(self, metric: MetricValue) -> bool:
        async with self._lock:
            self.exported_metrics.append(metric)
        return True

    async def export_audit(self, audit_event: AuditEvent) -> bool:
        async with self._lock:
            self.exported_audits.append(audit_event)
        return True

    async def flush(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def clear(self) -> None:
        """Clear collected non-audit telemetry items."""
        async with self._lock:
            self.exported_logs.clear()
            self.exported_traces.clear()
            self.exported_metrics.clear()
            # Note: Audits remain preserved for immutability contract where possible
