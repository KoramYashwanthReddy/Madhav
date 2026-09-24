"""Pydantic API Schemas (DTOs) for Module 33 — Observability & Audit."""

from datetime import datetime
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


class LogEntrySchema(BaseModel):
    timestamp: datetime
    level: LogLevel
    message: str
    service: str
    component: str
    module: str
    request_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    execution_id: str | None = None
    user_id: str | None = None
    event_name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    exception: dict[str, Any] | None = None
    environment: str
    version: str


class LogQueryResponseSchema(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[LogEntrySchema]


class MetricAggregationSchema(BaseModel):
    name: str
    metric_type: MetricType
    count: int
    sum: float
    min: float | None = None
    max: float | None = None
    avg: float | None = None
    p50: float | None = None
    p95: float | None = None
    p99: float | None = None
    unit: str
    labels: dict[str, str] = Field(default_factory=dict)


class MetricQueryResponseSchema(BaseModel):
    aggregations: list[MetricAggregationSchema]


class SpanSchema(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    span_type: SpanType
    name: str
    span_kind: SpanKind
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus
    status_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)


class TraceSummarySchema(BaseModel):
    trace_id: str
    root_span_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    execution_id: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus
    span_count: int
    error_count: int


class TraceListResponseSchema(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[TraceSummarySchema]


class TraceDetailResponseSchema(BaseModel):
    trace_id: str
    root_span_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    execution_id: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus
    span_count: int
    error_count: int
    spans: list[SpanSchema]


class ExecutionTimelineItemSchema(BaseModel):
    timestamp: datetime
    relative_offset_ms: float
    span_id: str
    span_name: str
    span_type: SpanType
    event_name: str
    status: SpanStatus
    duration_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ExecutionTimelineResponseSchema(BaseModel):
    execution_id: str
    trace_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    start_time: datetime
    total_duration_ms: float
    span_count: int
    items: list[ExecutionTimelineItemSchema]


class AuditEventSchema(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: AuditEventType
    actor: AuditActor
    actor_id: str
    target: str
    target_id: str | None = None
    action: str
    outcome: AuditOutcome
    severity: AuditSeverity
    category: AuditCategory
    reason: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    trace_id: str | None = None
    execution_id: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    retention_days: int
    retention_until: datetime | None = None
    status: AuditStatus


class AuditSearchResponseSchema(BaseModel):
    total: int
    offset: int
    limit: int
    items: list[AuditEventSchema]


class ComponentSchema(BaseModel):
    component_id: str
    name: str
    module: str
    version: str
    status: ComponentStatus
    description: str
    capabilities: list[str] = Field(default_factory=list)
    owner: str


class ComponentListResponseSchema(BaseModel):
    components: list[ComponentSchema]


class ErrorRecordSchema(BaseModel):
    error_id: str
    timestamp: datetime
    error_type: str
    message_safe: str
    component: str
    module: str
    operation: str
    trace_id: str | None = None
    span_id: str | None = None
    request_id: str | None = None
    execution_id: str | None = None
    stack_reference: str | None = None
    retryable: bool
    severity: LogLevel


class ErrorListResponseSchema(BaseModel):
    items: list[ErrorRecordSchema]


class StatisticsResponseSchema(BaseModel):
    total_requests_today: int
    total_errors_today: int
    avg_latency_ms: float
    p95_latency_ms: float
    active_traces_count: int
    total_spans_recorded: int
    total_logs_recorded: int
    total_metrics_recorded: int
    total_audit_events_recorded: int
    tool_executions_count: int
    agent_runs_count: int
    task_executions_count: int
    permission_denials_count: int
    security_events_count: int
    evaluation_runs_count: int
    automation_runs_count: int
    integration_failures_count: int


class HealthResponseSchema(BaseModel):
    is_healthy: bool
    storage_healthy: bool
    log_exporter_healthy: bool
    trace_exporter_healthy: bool
    metric_exporter_healthy: bool
    audit_storage_healthy: bool
    details: dict[str, Any] = Field(default_factory=dict)
