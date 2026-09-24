"""Domain models for Module 33 — Observability & Audit."""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.observability.domain.enums import (
    AuditActor,
    AuditCategory,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    AuditStatus,
    ComponentStatus,
    LogLevel,
    MetricType,
    SpanKind,
    SpanStatus,
    SpanType,
)


def generate_uuid() -> str:
    """Generate a standard UUID string."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(UTC)


class ObservabilityContext(BaseModel):
    """Context container for propagating correlation IDs across execution boundaries."""

    request_id: str = Field(default_factory=generate_uuid)
    correlation_id: str = Field(default_factory=generate_uuid)
    trace_id: str = Field(default_factory=generate_uuid)
    span_id: str = Field(default_factory=generate_uuid)
    execution_id: str = Field(default_factory=generate_uuid)
    user_id: str | None = None
    component: str = "core"
    operation: str = "unknown"
    environment: str = "development"
    version: str = "1.0.0"


class SpanEvent(BaseModel):
    """Structured event embedded inside a trace span."""

    timestamp: datetime = Field(default_factory=now_utc)
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class SpanLink(BaseModel):
    """Causal relationship link between trace spans."""

    trace_id: str
    span_id: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class Span(BaseModel):
    """OpenTelemetry-compatible trace span model."""

    span_id: str = Field(default_factory=generate_uuid)
    trace_id: str
    parent_span_id: str | None = None
    span_type: SpanType = SpanType.CUSTOM
    name: str
    span_kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = Field(default_factory=now_utc)
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus = SpanStatus.UNSET
    status_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[SpanEvent] = Field(default_factory=list)
    links: list[SpanLink] = Field(default_factory=list)


class Trace(BaseModel):
    """Complete trace containing root and child execution spans."""

    trace_id: str
    root_span_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    execution_id: str | None = None
    start_time: datetime = Field(default_factory=now_utc)
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus = SpanStatus.UNSET
    span_count: int = 0
    error_count: int = 0
    spans: list[Span] = Field(default_factory=list)


class StructuredLogEntry(BaseModel):
    """JSON-compatible structured log entry model."""

    timestamp: datetime = Field(default_factory=now_utc)
    level: LogLevel = LogLevel.INFO
    message: str
    service: str = "max-ai"
    component: str = "core"
    module: str = "module_33"
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    execution_id: str | None = None
    user_id: str | None = None
    event_name: str = "log_entry"
    attributes: dict[str, Any] = Field(default_factory=dict)
    exception: dict[str, Any] | None = None
    environment: str = "development"
    version: str = "1.0.0"


class MetricValue(BaseModel):
    """Single recorded metric data point."""

    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = Field(default_factory=now_utc)
    unit: str = "1"
    labels: dict[str, str] = Field(default_factory=dict)


class MetricAggregation(BaseModel):
    """Aggregated numerical metrics summary."""

    name: str
    metric_type: MetricType
    count: int = 0
    sum: float = 0.0
    min: float | None = None
    max: float | None = None
    avg: float | None = None
    p50: float | None = None
    p95: float | None = None
    p99: float | None = None
    rate_per_sec: float | None = None
    unit: str = "1"
    labels: dict[str, str] = Field(default_factory=dict)


class AuditEvidenceReference(BaseModel):
    """Reference link to evidence or snapshot stored out of band."""

    evidence_id: str
    evidence_type: str
    uri: str | None = None
    content_hash: str | None = None


class AuditMetadata(BaseModel):
    """Auxiliary non-sensitive audit metadata."""

    ip_address: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    """Immutable audit record for security, system, and business actions."""

    event_id: str = Field(default_factory=generate_uuid)
    timestamp: datetime = Field(default_factory=now_utc)
    event_type: AuditEventType
    actor: AuditActor
    actor_id: str = "system"
    target: str
    target_id: str | None = None
    action: str
    outcome: AuditOutcome = AuditOutcome.SUCCESS
    severity: AuditSeverity = AuditSeverity.INFO
    category: AuditCategory = AuditCategory.SYSTEM
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    evidence: list[AuditEvidenceReference] = Field(default_factory=list)
    metadata: AuditMetadata = Field(default_factory=AuditMetadata)
    correlation_id: str | None = None
    trace_id: str | None = None
    execution_id: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    retention_days: int = 90
    retention_until: datetime | None = None
    status: AuditStatus = AuditStatus.PERSISTED


class ExecutionTimelineItem(BaseModel):
    """Single event node on an execution timeline."""

    timestamp: datetime
    relative_offset_ms: float
    span_id: str
    span_name: str
    span_type: SpanType
    event_name: str
    status: SpanStatus
    duration_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExecutionTimeline(BaseModel):
    """Derived sequence of execution events across modules."""

    execution_id: str
    trace_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    start_time: datetime = Field(default_factory=now_utc)
    total_duration_ms: float = 0.0
    span_count: int = 0
    items: list[ExecutionTimelineItem] = Field(default_factory=list)


class ErrorRecord(BaseModel):
    """Structured representation of system or execution errors."""

    error_id: str = Field(default_factory=generate_uuid)
    timestamp: datetime = Field(default_factory=now_utc)
    error_type: str
    message_safe: str
    component: str = "core"
    module: str = "module_33"
    operation: str = "unknown"
    trace_id: str | None = None
    span_id: str | None = None
    request_id: str | None = None
    execution_id: str | None = None
    stack_reference: str | None = None
    retryable: bool = False
    severity: LogLevel = LogLevel.ERROR
    cause_reference: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ObservableComponent(BaseModel):
    """Registry entry describing an observable system component."""

    component_id: str
    name: str
    module: str
    version: str = "1.0.0"
    status: ComponentStatus = ComponentStatus.HEALTHY
    description: str = ""
    health_endpoint: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    owner: str = "system"


class ObservabilityHealthStatus(BaseModel):
    """Health check response status for observability services."""

    is_healthy: bool = True
    storage_healthy: bool = True
    log_exporter_healthy: bool = True
    trace_exporter_healthy: bool = True
    metric_exporter_healthy: bool = True
    audit_storage_healthy: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class ObservabilityStatistics(BaseModel):
    """Aggregated operational telemetry statistics summary."""

    total_requests_today: int = 0
    total_errors_today: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    active_traces_count: int = 0
    total_spans_recorded: int = 0
    total_logs_recorded: int = 0
    total_metrics_recorded: int = 0
    total_audit_events_recorded: int = 0
    tool_executions_count: int = 0
    agent_runs_count: int = 0
    task_executions_count: int = 0
    permission_denials_count: int = 0
    security_events_count: int = 0
    evaluation_runs_count: int = 0
    automation_runs_count: int = 0
    integration_failures_count: int = 0
