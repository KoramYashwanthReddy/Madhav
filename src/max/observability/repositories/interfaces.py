"""Repository interfaces for Module 33 — Observability & Audit."""

from abc import ABC, abstractmethod
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


class LogRepository(ABC):
    """Abstract interface for storing and querying structured log entries."""

    @abstractmethod
    async def append(self, log_entry: StructuredLogEntry) -> None:
        """Append a structured log record."""
        pass

    @abstractmethod
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
        """Query structured log entries with filtering."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total stored log entries."""
        pass


class MetricRepository(ABC):
    """Abstract interface for metrics storage and aggregation."""

    @abstractmethod
    async def record(self, metric: MetricValue) -> None:
        """Record a single metric observation."""
        pass

    @abstractmethod
    async def get_aggregations(
        self,
        name: str | None = None,
        metric_type: MetricType | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[MetricAggregation]:
        """Get metric summaries and statistical aggregations."""
        pass

    @abstractmethod
    async def get_all_raw(self, limit: int = 1000) -> list[MetricValue]:
        """Get raw metric observations."""
        pass


class SpanRepository(ABC):
    """Abstract interface for span storage."""

    @abstractmethod
    async def save_span(self, span: Span) -> None:
        """Save or update an execution span."""
        pass

    @abstractmethod
    async def get_span(self, span_id: str) -> Span | None:
        """Get span by unique span ID."""
        pass

    @abstractmethod
    async def get_spans_by_trace(self, trace_id: str) -> list[Span]:
        """Get all spans associated with a trace ID."""
        pass


class TraceRepository(ABC):
    """Abstract interface for trace storage and search."""

    @abstractmethod
    async def save_trace(self, trace: Trace) -> None:
        """Save or update a trace."""
        pass

    @abstractmethod
    async def get_trace(self, trace_id: str) -> Trace | None:
        """Get trace by trace ID."""
        pass

    @abstractmethod
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
        """Search traces matching filter parameters."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total stored traces."""
        pass


class AuditEventRepository(ABC):
    """Abstract interface for append-only audit event persistence."""

    @abstractmethod
    async def append(self, event: AuditEvent) -> None:
        """Append an immutable audit record."""
        pass

    @abstractmethod
    async def get_by_id(self, event_id: str) -> AuditEvent | None:
        """Get single audit event by ID."""
        pass

    @abstractmethod
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
        """Search immutable audit events with pagination and filtering."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total stored audit events."""
        pass


class ErrorRepository(ABC):
    """Abstract interface for error record storage."""

    @abstractmethod
    async def record_error(self, error: ErrorRecord) -> None:
        """Record an exception/error incident."""
        pass

    @abstractmethod
    async def get_errors(
        self,
        component: str | None = None,
        module: str | None = None,
        severity: LogLevel | None = None,
        trace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ErrorRecord]:
        """Query stored errors."""
        pass


class ComponentRepository(ABC):
    """Abstract interface for observable system component registry."""

    @abstractmethod
    async def register(self, component: ObservableComponent) -> None:
        """Register or update an observable system component."""
        pass

    @abstractmethod
    async def get(self, component_id: str) -> ObservableComponent | None:
        """Get component metadata by ID."""
        pass

    @abstractmethod
    async def list_all(self) -> list[ObservableComponent]:
        """List all registered components."""
        pass


class ExecutionRepository(ABC):
    """Abstract interface for storing and retrieving execution timelines."""

    @abstractmethod
    async def save_timeline(self, timeline: ExecutionTimeline) -> None:
        """Save execution timeline."""
        pass

    @abstractmethod
    async def get_timeline(self, execution_id: str) -> ExecutionTimeline | None:
        """Get timeline by execution ID."""
        pass
