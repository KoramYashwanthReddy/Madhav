"""InMemory repository implementations for Module 33 — Observability & Audit."""

import asyncio
from datetime import datetime

from max.observability.domain.enums import (
    AuditActor,
    AuditCategory,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    LogLevel,
    MetricType,
    SpanStatus,
)
from max.observability.domain.exceptions import AuditImmutabilityError
from max.observability.domain.models import (
    AuditEvent,
    ErrorRecord,
    ExecutionTimeline,
    MetricAggregation,
    MetricValue,
    ObservableComponent,
    Span,
    StructuredLogEntry,
    Trace,
)
from max.observability.repositories.interfaces import (
    AuditEventRepository,
    ComponentRepository,
    ErrorRepository,
    ExecutionRepository,
    LogRepository,
    MetricRepository,
    SpanRepository,
    TraceRepository,
)


class InMemoryLogRepository(LogRepository):
    """In-memory thread-safe implementation of LogRepository."""

    def __init__(self, max_capacity: int = 10000) -> None:
        self._logs: list[StructuredLogEntry] = []
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def append(self, log_entry: StructuredLogEntry) -> None:
        async with self._lock:
            if len(self._logs) >= self._max_capacity:
                self._logs.pop(0)  # Evict oldest entry
            self._logs.append(log_entry)

    async def query(
        self,
        level: LogLevel | None = None,
        component: str | None = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        execution_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StructuredLogEntry]:
        async with self._lock:
            results = list(self._logs)

        if level is not None:
            results = [log for log in results if log.level == level]
        if component is not None:
            results = [log for log in results if log.component == component]
        if request_id is not None:
            results = [log for log in results if log.request_id == request_id]
        if correlation_id is not None:
            results = [log for log in results if log.correlation_id == correlation_id]
        if trace_id is not None:
            results = [log for log in results if log.trace_id == trace_id]
        if execution_id is not None:
            results = [log for log in results if log.execution_id == execution_id]
        if start_time is not None:
            results = [log for log in results if log.timestamp >= start_time]
        if end_time is not None:
            results = [log for log in results if log.timestamp <= end_time]

        # Reverse chronological ordering (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[offset : offset + limit]

    async def count(self) -> int:
        async with self._lock:
            return len(self._logs)


class InMemoryMetricRepository(MetricRepository):
    """In-memory thread-safe implementation of MetricRepository."""

    def __init__(self, max_capacity: int = 50000) -> None:
        self._metrics: list[MetricValue] = []
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def record(self, metric: MetricValue) -> None:
        async with self._lock:
            if len(self._metrics) >= self._max_capacity:
                self._metrics.pop(0)
            self._metrics.append(metric)

    async def get_aggregations(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[MetricAggregation]:
        async with self._lock:
            metrics_copy = list(self._metrics)

        # Filter metrics
        filtered = metrics_copy
        if name is not None:
            filtered = [m for m in filtered if m.name == name]
        if metric_type is not None:
            filtered = [m for m in filtered if m.metric_type == metric_type]
        if labels:
            filtered = [
                m for m in filtered if all(m.labels.get(k) == v for k, v in labels.items())
            ]

        # Group by name and metric_type
        grouped: dict[tuple[str, MetricType], list[MetricValue]] = {}
        for m in filtered:
            key = (m.name, m.metric_type)
            grouped.setdefault(key, []).append(m)

        aggregations: list[MetricAggregation] = []
        for (m_name, m_type), values in grouped.items():
            vals = [v.value for v in values]
            if not vals:
                continue
            vals_sorted = sorted(vals)
            cnt = len(vals)
            s = sum(vals)
            mn = vals_sorted[0]
            mx = vals_sorted[-1]
            avg = s / cnt

            p50 = vals_sorted[int(cnt * 0.50)]
            p95 = vals_sorted[int(cnt * 0.95)] if cnt >= 1 else mx
            p99 = vals_sorted[int(cnt * 0.99)] if cnt >= 1 else mx

            sample_labels = values[-1].labels if values else {}
            sample_unit = values[-1].unit if values else "1"

            aggregations.append(
                MetricAggregation(
                    name=m_name,
                    metric_type=m_type,
                    count=cnt,
                    sum=s,
                    min=mn,
                    max=mx,
                    avg=avg,
                    p50=p50,
                    p95=p95,
                    p99=p99,
                    unit=sample_unit,
                    labels=sample_labels,
                )
            )

        return aggregations

    async def get_all_raw(self, limit: int = 1000) -> list[MetricValue]:
        async with self._lock:
            return list(reversed(self._metrics[-limit:]))


class InMemorySpanRepository(SpanRepository):
    """In-memory thread-safe implementation of SpanRepository."""

    def __init__(self) -> None:
        self._spans: dict[str, Span] = {}
        self._lock = asyncio.Lock()

    async def save_span(self, span: Span) -> None:
        async with self._lock:
            self._spans[span.span_id] = span

    async def get_span(self, span_id: str) -> Span | None:
        async with self._lock:
            return self._spans.get(span_id)

    async def get_spans_by_trace(self, trace_id: str) -> list[Span]:
        async with self._lock:
            return [s for s in self._spans.values() if s.trace_id == trace_id]


class InMemoryTraceRepository(TraceRepository):
    """In-memory thread-safe implementation of TraceRepository."""

    def __init__(self, max_capacity: int = 5000) -> None:
        self._traces: dict[str, Trace] = {}
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def save_trace(self, trace: Trace) -> None:
        async with self._lock:
            if len(self._traces) >= self._max_capacity and trace.trace_id not in self._traces:
                oldest_key = next(iter(self._traces))
                del self._traces[oldest_key]
            self._traces[trace.trace_id] = trace

    async def get_trace(self, trace_id: str) -> Trace | None:
        async with self._lock:
            return self._traces.get(trace_id)

    async def search_traces(
        self,
        request_id: str | None = None,
        correlation_id: str | None = None,
        execution_id: str | None = None,
        status: SpanStatus | None = None,
        has_error: bool | None = None,
        min_duration_ms: float | None = None,
        max_duration_ms: float | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Trace]:
        async with self._lock:
            results = list(self._traces.values())

        if request_id is not None:
            results = [t for t in results if t.request_id == request_id]
        if correlation_id is not None:
            results = [t for t in results if t.correlation_id == correlation_id]
        if execution_id is not None:
            results = [t for t in results if t.execution_id == execution_id]
        if status is not None:
            results = [t for t in results if t.status == status]
        if has_error is True:
            results = [t for t in results if t.error_count > 0 or t.status == SpanStatus.ERROR]
        elif has_error is False:
            results = [t for t in results if t.error_count == 0 and t.status != SpanStatus.ERROR]
        if min_duration_ms is not None:
            results = [
                t for t in results if t.duration_ms is not None and t.duration_ms >= min_duration_ms
            ]
        if max_duration_ms is not None:
            results = [
                t for t in results if t.duration_ms is not None and t.duration_ms <= max_duration_ms
            ]
        if start_time is not None:
            results = [t for t in results if t.start_time >= start_time]
        if end_time is not None:
            results = [t for t in results if t.start_time <= end_time]

        results.sort(key=lambda x: x.start_time, reverse=True)
        return results[offset : offset + limit]

    async def count(self) -> int:
        async with self._lock:
            return len(self._traces)


class InMemoryAuditEventRepository(AuditEventRepository):
    """In-memory append-only implementation of AuditEventRepository.

    Strictly preserves immutability of recorded security and system audit events.
    """

    def __init__(self, max_capacity: int = 20000) -> None:
        self._events: list[AuditEvent] = []
        self._event_map: dict[str, AuditEvent] = {}
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def append(self, event: AuditEvent) -> None:
        async with self._lock:
            if event.event_id in self._event_map:
                raise AuditImmutabilityError(
                    f"Cannot overwrite existing audit event {event.event_id}. Audit logs are append-only.",
                    details={"event_id": event.event_id},
                )
            if len(self._events) >= self._max_capacity:
                oldest = self._events.pop(0)
                self._event_map.pop(oldest.event_id, None)

            self._events.append(event)
            self._event_map[event.event_id] = event

    async def get_by_id(self, event_id: str) -> AuditEvent | None:
        async with self._lock:
            return self._event_map.get(event_id)

    async def search(
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
        async with self._lock:
            results = list(self._events)

        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]
        if actor is not None:
            results = [e for e in results if e.actor == actor]
        if actor_id is not None:
            results = [e for e in results if e.actor_id == actor_id]
        if target is not None:
            results = [e for e in results if e.target == target]
        if outcome is not None:
            results = [e for e in results if e.outcome == outcome]
        if severity is not None:
            results = [e for e in results if e.severity == severity]
        if category is not None:
            results = [e for e in results if e.category == category]
        if correlation_id is not None:
            results = [e for e in results if e.correlation_id == correlation_id]
        if trace_id is not None:
            results = [e for e in results if e.trace_id == trace_id]
        if execution_id is not None:
            results = [e for e in results if e.execution_id == execution_id]
        if request_id is not None:
            results = [e for e in results if e.request_id == request_id]
        if user_id is not None:
            results = [e for e in results if e.user_id == user_id]
        if start_time is not None:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time is not None:
            results = [e for e in results if e.timestamp <= end_time]

        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[offset : offset + limit]

    async def count(self) -> int:
        async with self._lock:
            return len(self._events)


class InMemoryErrorRepository(ErrorRepository):
    """In-memory implementation of ErrorRepository."""

    def __init__(self, max_capacity: int = 5000) -> None:
        self._errors: list[ErrorRecord] = []
        self._max_capacity = max_capacity
        self._lock = asyncio.Lock()

    async def record_error(self, error: ErrorRecord) -> None:
        async with self._lock:
            if len(self._errors) >= self._max_capacity:
                self._errors.pop(0)
            self._errors.append(error)

    async def get_errors(
        self,
        component: str | None = None,
        module: str | None = None,
        severity: LogLevel | None = None,
        trace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ErrorRecord]:
        async with self._lock:
            results = list(self._errors)

        if component is not None:
            results = [e for e in results if e.component == component]
        if module is not None:
            results = [e for e in results if e.module == module]
        if severity is not None:
            results = [e for e in results if e.severity == severity]
        if trace_id is not None:
            results = [e for e in results if e.trace_id == trace_id]

        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[offset : offset + limit]


class InMemoryComponentRepository(ComponentRepository):
    """In-memory implementation of ComponentRepository."""

    def __init__(self) -> None:
        self._components: dict[str, ObservableComponent] = {}
        self._lock = asyncio.Lock()

    async def register(self, component: ObservableComponent) -> None:
        async with self._lock:
            self._components[component.component_id] = component

    async def get(self, component_id: str) -> ObservableComponent | None:
        async with self._lock:
            return self._components.get(component_id)

    async def list_all(self) -> list[ObservableComponent]:
        async with self._lock:
            return list(self._components.values())


class InMemoryExecutionRepository(ExecutionRepository):
    """In-memory implementation of ExecutionRepository."""

    def __init__(self) -> None:
        self._timelines: dict[str, ExecutionTimeline] = {}
        self._lock = asyncio.Lock()

    async def save_timeline(self, timeline: ExecutionTimeline) -> None:
        async with self._lock:
            self._timelines[timeline.execution_id] = timeline

    async def get_timeline(self, execution_id: str) -> ExecutionTimeline | None:
        async with self._lock:
            return self._timelines.get(execution_id)
