"""Provider-neutral metrics service with high-cardinality protection for Module 33."""

import time
from typing import Any

from max.observability.domain.enums import MetricType
from max.observability.domain.models import MetricValue, now_utc
from max.observability.exporters.base import TelemetryExporter
from max.observability.repositories.interfaces import MetricRepository

ALLOWED_LABEL_KEYS = {
    "module",
    "operation",
    "status",
    "provider",
    "environment",
    "tool_category",
    "evaluation_type",
    "agent_type",
    "component",
    "outcome",
    "method",
    "status_code",
    "error_type",
}

MAX_LABEL_VALUE_LENGTH = 64


class MetricsService:
    """Telemetry metrics recording service with cardinality bounds enforcement."""

    def __init__(
        self,
        repository: MetricRepository,
        exporter: TelemetryExporter | None = None,
        enabled: bool = True,
    ) -> None:
        self.repository = repository
        self.exporter = exporter
        self.enabled = enabled

    def sanitize_labels(self, labels: dict[str, Any] | None) -> dict[str, str]:
        """Filter and sanitize label dictionaries to prevent high-cardinality metric explosions."""
        if not labels:
            return {}

        sanitized: dict[str, str] = {}
        for key, val in labels.items():
            norm_key = str(key).lower().strip()
            # Enforce bounded label whitelist where possible or truncate
            if norm_key in ALLOWED_LABEL_KEYS or len(sanitized) < 10:
                val_str = str(val).strip()[:MAX_LABEL_VALUE_LENGTH]
                sanitized[norm_key] = val_str
        return sanitized

    async def record_metric(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        unit: str = "1",
        labels: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a raw metric data point."""
        clean_labels = self.sanitize_labels(labels)
        metric = MetricValue(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=now_utc(),
            unit=unit,
            labels=clean_labels,
        )

        if self.enabled:
            await self.repository.record(metric)
            if self.exporter:
                try:
                    await self.exporter.export_metric(metric)
                except Exception:
                    pass

        return metric

    async def counter_increment(
        self,
        name: str,
        value: float = 1.0,
        unit: str = "1",
        labels: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Increment a counter metric."""
        return await self.record_metric(name, MetricType.COUNTER, value, unit=unit, labels=labels)

    async def gauge_set(
        self,
        name: str,
        value: float,
        unit: str = "1",
        labels: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Set a gauge metric value."""
        return await self.record_metric(name, MetricType.GAUGE, value, unit=unit, labels=labels)

    async def histogram_observe(
        self,
        name: str,
        value: float,
        unit: str = "ms",
        labels: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Observe a histogram sample."""
        return await self.record_metric(name, MetricType.HISTOGRAM, value, unit=unit, labels=labels)

    async def timer_record(
        self,
        name: str,
        duration_ms: float,
        labels: dict[str, Any] | None = None,
    ) -> MetricValue:
        """Record a timer measurement in milliseconds."""
        return await self.record_metric(name, MetricType.TIMER, duration_ms, unit="ms", labels=labels)


class TimerContext:
    """Helper context manager to measure execution duration in milliseconds."""

    def __init__(
        self,
        metrics_service: MetricsService,
        name: str,
        labels: dict[str, Any] | None = None,
    ) -> None:
        self.metrics_service = metrics_service
        self.name = name
        self.labels = labels
        self.start_time: float = 0.0
        self.duration_ms: float = 0.0

    async def __aenter__(self) -> "TimerContext":
        self.start_time = time.perf_counter()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        end_time = time.perf_counter()
        self.duration_ms = (end_time - self.start_time) * 1000.0
        await self.metrics_service.timer_record(self.name, self.duration_ms, labels=self.labels)
