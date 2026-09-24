"""Console telemetry exporter for Module 33 — Observability & Audit."""

import sys
from typing import Any

from max.observability.domain.models import (
    AuditEvent,
    MetricValue,
    StructuredLogEntry,
    Trace,
)
from max.observability.exporters.base import TelemetryExporter


class ConsoleExporter(TelemetryExporter):
    """Outputs telemetry records to stdout/stderr in structured JSON or text."""

    def __init__(self, json_format: bool = True, stream: Any = None) -> None:
        self.json_format = json_format
        self.stream = stream or sys.stdout

    async def export_log(self, log_entry: StructuredLogEntry) -> bool:
        if self.json_format:
            payload = log_entry.model_dump_json()
            self.stream.write(f"[LOG] {payload}\n")
        else:
            self.stream.write(
                f"[{log_entry.timestamp.isoformat()}] [{log_entry.level}] {log_entry.message} (trace_id={log_entry.trace_id})\n"
            )
        self.stream.flush()
        return True

    async def export_trace(self, trace: Trace) -> bool:
        if self.json_format:
            payload = trace.model_dump_json()
            self.stream.write(f"[TRACE] {payload}\n")
        else:
            self.stream.write(
                f"[TRACE] ID={trace.trace_id} spans={trace.span_count} status={trace.status}\n"
            )
        self.stream.flush()
        return True

    async def export_metric(self, metric: MetricValue) -> bool:
        if self.json_format:
            payload = metric.model_dump_json()
            self.stream.write(f"[METRIC] {payload}\n")
        else:
            self.stream.write(
                f"[METRIC] {metric.name}={metric.value} labels={metric.labels}\n"
            )
        self.stream.flush()
        return True

    async def export_audit(self, audit_event: AuditEvent) -> bool:
        payload = audit_event.model_dump_json()
        self.stream.write(f"[AUDIT] {payload}\n")
        self.stream.flush()
        return True

    async def flush(self) -> None:
        self.stream.flush()

    async def close(self) -> None:
        await self.flush()
