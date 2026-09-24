"""FastAPI Route Handlers for Module 33 — Observability & Audit."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from max.observability.container import ObservabilityContainer
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
from max.observability.schemas.schemas import (
    AuditEventSchema,
    AuditSearchResponseSchema,
    ComponentListResponseSchema,
    ComponentSchema,
    ErrorListResponseSchema,
    ErrorRecordSchema,
    ExecutionTimelineItemSchema,
    ExecutionTimelineResponseSchema,
    HealthResponseSchema,
    LogEntrySchema,
    LogQueryResponseSchema,
    MetricAggregationSchema,
    MetricQueryResponseSchema,
    SpanSchema,
    StatisticsResponseSchema,
    TraceDetailResponseSchema,
    TraceListResponseSchema,
    TraceSummarySchema,
)
from max.observability.services.observability_service import ObservabilityService

router = APIRouter(prefix="/observability", tags=["Observability & Audit"])


def get_observability_service() -> ObservabilityService:
    """Dependency provider for ObservabilityService."""
    return ObservabilityContainer.get_instance().observability_service


@router.get(
    "/health",
    response_model=HealthResponseSchema,
    summary="Get Observability subsystem health status",
)
async def get_health() -> HealthResponseSchema:
    """Return health and exporter readiness information for observability services."""
    service = get_observability_service()
    health = await service.get_health_status()
    return HealthResponseSchema(
        is_healthy=health.is_healthy,
        storage_healthy=health.storage_healthy,
        log_exporter_healthy=health.log_exporter_healthy,
        trace_exporter_healthy=health.trace_exporter_healthy,
        metric_exporter_healthy=health.metric_exporter_healthy,
        audit_storage_healthy=health.audit_storage_healthy,
        details=health.details,
    )


@router.get(
    "/logs",
    response_model=LogQueryResponseSchema,
    summary="Search structured log records",
)
async def search_logs(
    level: LogLevel | None = Query(None, description="Minimum log level filter"),
    component: str | None = Query(None, description="Component name filter"),
    request_id: str | None = Query(None, description="Request ID correlation filter"),
    correlation_id: str | None = Query(None, description="Correlation ID filter"),
    trace_id: str | None = Query(None, description="Trace ID filter"),
    execution_id: str | None = Query(None, description="Execution ID filter"),
    start_time: datetime | None = Query(None, description="Start time UTC"),
    end_time: datetime | None = Query(None, description="End time UTC"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> LogQueryResponseSchema:
    """Query structured, secret-redacted log entries."""
    service = get_observability_service()
    logs = await service.log_repository.query(
        level=level,
        component=component,
        request_id=request_id,
        correlation_id=correlation_id,
        trace_id=trace_id,
        execution_id=execution_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    total = await service.log_repository.count()

    items = [
        LogEntrySchema(
            timestamp=entry.timestamp,
            level=entry.level,
            message=entry.message,
            service=entry.service,
            component=entry.component,
            module=entry.module,
            request_id=entry.request_id,
            correlation_id=entry.correlation_id,
            trace_id=entry.trace_id,
            span_id=entry.span_id,
            execution_id=entry.execution_id,
            user_id=entry.user_id,
            event_name=entry.event_name,
            attributes=entry.attributes,
            exception=entry.exception,
            environment=entry.environment,
            version=entry.version,
        )
        for entry in logs
    ]

    return LogQueryResponseSchema(total=total, offset=offset, limit=limit, items=items)


@router.get(
    "/metrics",
    response_model=MetricQueryResponseSchema,
    summary="Query metric aggregations",
)
async def query_metrics(
    name: str | None = Query(None, description="Metric name filter"),
    metric_type: MetricType | None = Query(None, description="Metric type filter"),
) -> MetricQueryResponseSchema:
    """Retrieve summarized telemetry metrics with high-cardinality label bounds."""
    service = get_observability_service()
    aggs = await service.metric_repository.get_aggregations(name=name, metric_type=metric_type)

    items = [
        MetricAggregationSchema(
            name=a.name,
            metric_type=a.metric_type,
            count=a.count,
            sum=a.sum,
            min=a.min,
            max=a.max,
            avg=a.avg,
            p50=a.p50,
            p95=a.p95,
            p99=a.p99,
            unit=a.unit,
            labels=a.labels,
        )
        for a in aggs
    ]

    return MetricQueryResponseSchema(aggregations=items)


@router.get(
    "/traces",
    response_model=TraceListResponseSchema,
    summary="Search distributed execution traces",
)
async def search_traces(
    request_id: str | None = Query(None, description="Request ID filter"),
    correlation_id: str | None = Query(None, description="Correlation ID filter"),
    execution_id: str | None = Query(None, description="Execution ID filter"),
    status: SpanStatus | None = Query(None, description="Span status filter"),
    has_error: bool | None = Query(None, description="Filter traces containing errors"),
    min_duration_ms: float | None = Query(None, description="Minimum trace duration in ms"),
    max_duration_ms: float | None = Query(None, description="Maximum trace duration in ms"),
    start_time: datetime | None = Query(None, description="Start time UTC"),
    end_time: datetime | None = Query(None, description="End time UTC"),
    limit: int = Query(50, ge=1, le=500, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> TraceListResponseSchema:
    """Search trace execution records across system modules."""
    service = get_observability_service()
    traces = await service.trace_repository.search_traces(
        request_id=request_id,
        correlation_id=correlation_id,
        execution_id=execution_id,
        status=status,
        has_error=has_error,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    total = await service.trace_repository.count()

    items = [
        TraceSummarySchema(
            trace_id=t.trace_id,
            root_span_id=t.root_span_id,
            request_id=t.request_id,
            correlation_id=t.correlation_id,
            execution_id=t.execution_id,
            start_time=t.start_time,
            end_time=t.end_time,
            duration_ms=t.duration_ms,
            status=t.status,
            span_count=t.span_count,
            error_count=t.error_count,
        )
        for t in traces
    ]

    return TraceListResponseSchema(total=total, offset=offset, limit=limit, items=items)


@router.get(
    "/traces/{trace_id}",
    response_model=TraceDetailResponseSchema,
    summary="Get detailed trace by trace ID",
)
async def get_trace_detail(trace_id: str) -> TraceDetailResponseSchema:
    """Get complete trace metadata and child execution spans."""
    service = get_observability_service()
    trace = await service.trace_repository.get_trace(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace with ID '{trace_id}' not found.",
        )

    spans = [
        SpanSchema(
            span_id=s.span_id,
            trace_id=s.trace_id,
            parent_span_id=s.parent_span_id,
            span_type=s.span_type,
            name=s.name,
            span_kind=s.span_kind,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_ms=s.duration_ms,
            status=s.status,
            status_message=s.status_message,
            attributes=s.attributes,
            events=[{"name": e.name, "timestamp": e.timestamp, "attributes": e.attributes} for e in s.events],
        )
        for s in trace.spans
    ]

    return TraceDetailResponseSchema(
        trace_id=trace.trace_id,
        root_span_id=trace.root_span_id,
        request_id=trace.request_id,
        correlation_id=trace.correlation_id,
        execution_id=trace.execution_id,
        start_time=trace.start_time,
        end_time=trace.end_time,
        duration_ms=trace.duration_ms,
        status=trace.status,
        span_count=trace.span_count,
        error_count=trace.error_count,
        spans=spans,
    )


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionTimelineResponseSchema,
    summary="Get derived execution timeline for an execution ID",
)
async def get_execution_timeline(execution_id: str) -> ExecutionTimelineResponseSchema:
    """Retrieve derived step-by-step execution timeline across components."""
    service = get_observability_service()
    timeline = await service.get_execution_timeline(execution_id)
    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution timeline for ID '{execution_id}' not found.",
        )

    items = [
        ExecutionTimelineItemSchema(
            timestamp=it.timestamp,
            relative_offset_ms=it.relative_offset_ms,
            span_id=it.span_id,
            span_name=it.span_name,
            span_type=it.span_type,
            event_name=it.event_name,
            status=it.status,
            duration_ms=it.duration_ms,
            details=it.details,
        )
        for it in timeline.items
    ]

    return ExecutionTimelineResponseSchema(
        execution_id=timeline.execution_id,
        trace_id=timeline.trace_id,
        request_id=timeline.request_id,
        correlation_id=timeline.correlation_id,
        start_time=timeline.start_time,
        total_duration_ms=timeline.total_duration_ms,
        span_count=timeline.span_count,
        items=items,
    )


audit_router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "/audit",
    response_model=AuditSearchResponseSchema,
    summary="Search append-only audit records",
)
@audit_router.get(
    "/logs",
    response_model=AuditSearchResponseSchema,
    summary="Search append-only audit records",
)
@audit_router.get(
    "",
    response_model=AuditSearchResponseSchema,
    summary="Search append-only audit records",
)
async def search_audit_records(
    event_type: AuditEventType | None = Query(None, description="Audit event type filter"),
    actor: AuditActor | None = Query(None, description="Audit actor category filter"),
    actor_id: str | None = Query(None, description="Actor ID filter"),
    target: str | None = Query(None, description="Target domain filter"),
    outcome: AuditOutcome | None = Query(None, description="Audit outcome filter"),
    severity: AuditSeverity | None = Query(None, description="Audit severity filter"),
    category: AuditCategory | None = Query(None, description="Audit category filter"),
    correlation_id: str | None = Query(None, description="Correlation ID filter"),
    trace_id: str | None = Query(None, description="Trace ID filter"),
    execution_id: str | None = Query(None, description="Execution ID filter"),
    request_id: str | None = Query(None, description="Request ID filter"),
    user_id: str | None = Query(None, description="User reference filter"),
    start_time: datetime | None = Query(None, description="Start time UTC"),
    end_time: datetime | None = Query(None, description="End time UTC"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> AuditSearchResponseSchema:
    """Search immutable audit records for security, system, and business accountability."""
    service = get_observability_service()
    events = await service.audit.search_events(
        event_type=event_type,
        actor=actor,
        actor_id=actor_id,
        target=target,
        outcome=outcome,
        severity=severity,
        category=category,
        correlation_id=correlation_id,
        trace_id=trace_id,
        execution_id=execution_id,
        request_id=request_id,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    total = await service.audit_repository.count()

    items = [
        AuditEventSchema(
            event_id=e.event_id,
            timestamp=e.timestamp,
            event_type=e.event_type,
            actor=e.actor,
            actor_id=e.actor_id,
            target=e.target,
            target_id=e.target_id,
            action=e.action,
            outcome=e.outcome,
            severity=e.severity,
            category=e.category,
            reason=e.reason,
            details=e.details,
            correlation_id=e.correlation_id,
            trace_id=e.trace_id,
            execution_id=e.execution_id,
            request_id=e.request_id,
            user_id=e.user_id,
            retention_days=e.retention_days,
            retention_until=e.retention_until,
            status=e.status,
        )
        for e in events
    ]

    return AuditSearchResponseSchema(total=total, offset=offset, limit=limit, items=items)


@router.get(
    "/audit/{event_id}",
    response_model=AuditEventSchema,
    summary="Get audit event by ID",
)
async def get_audit_event_detail(event_id: str) -> AuditEventSchema:
    """Retrieve single append-only audit event record."""
    service = get_observability_service()
    event = await service.audit.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit event with ID '{event_id}' not found.",
        )

    return AuditEventSchema(
        event_id=event.event_id,
        timestamp=event.timestamp,
        event_type=event.event_type,
        actor=event.actor,
        actor_id=event.actor_id,
        target=event.target,
        target_id=event.target_id,
        action=event.action,
        outcome=event.outcome,
        severity=event.severity,
        category=event.category,
        reason=event.reason,
        details=event.details,
        correlation_id=event.correlation_id,
        trace_id=event.trace_id,
        execution_id=event.execution_id,
        request_id=event.request_id,
        user_id=event.user_id,
        retention_days=event.retention_days,
        retention_until=event.retention_until,
        status=event.status,
    )


@router.get(
    "/components",
    response_model=ComponentListResponseSchema,
    summary="List observable system components",
)
async def list_components() -> ComponentListResponseSchema:
    """List registered observable components and health metadata."""
    service = get_observability_service()
    components = await service.component_repository.list_all()

    items = [
        ComponentSchema(
            component_id=c.component_id,
            name=c.name,
            module=c.module,
            version=c.version,
            status=c.status,
            description=c.description,
            capabilities=c.capabilities,
            owner=c.owner,
        )
        for c in components
    ]

    return ComponentListResponseSchema(components=items)


@router.get(
    "/errors",
    response_model=ErrorListResponseSchema,
    summary="Query error tracking records",
)
async def list_errors(
    component: str | None = Query(None, description="Component filter"),
    module: str | None = Query(None, description="Module filter"),
    severity: LogLevel | None = Query(None, description="Severity filter"),
    trace_id: str | None = Query(None, description="Trace ID filter"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
) -> ErrorListResponseSchema:
    """Query recorded exception and error tracking records."""
    service = get_observability_service()
    errors = await service.error_tracking.get_errors(
        component=component,
        module=module,
        severity=severity,
        trace_id=trace_id,
        limit=limit,
        offset=offset,
    )

    items = [
        ErrorRecordSchema(
            error_id=e.error_id,
            timestamp=e.timestamp,
            error_type=e.error_type,
            message_safe=e.message_safe,
            component=e.component,
            module=e.module,
            operation=e.operation,
            trace_id=e.trace_id,
            span_id=e.span_id,
            request_id=e.request_id,
            execution_id=e.execution_id,
            stack_reference=e.stack_reference,
            retryable=e.retryable,
            severity=e.severity,
        )
        for e in errors
    ]

    return ErrorListResponseSchema(items=items)


@router.get(
    "/statistics",
    response_model=StatisticsResponseSchema,
    summary="Get system operational statistics",
)
async def get_statistics() -> StatisticsResponseSchema:
    """Retrieve operational telemetry statistics for dashboard and Monitoring consumption."""
    service = get_observability_service()
    stats = await service.get_statistics()
    return StatisticsResponseSchema(
        total_requests_today=stats.total_requests_today,
        total_errors_today=stats.total_errors_today,
        avg_latency_ms=stats.avg_latency_ms,
        p95_latency_ms=stats.p95_latency_ms,
        active_traces_count=stats.active_traces_count,
        total_spans_recorded=stats.total_spans_recorded,
        total_logs_recorded=stats.total_logs_recorded,
        total_metrics_recorded=stats.total_metrics_recorded,
        total_audit_events_recorded=stats.total_audit_events_recorded,
        tool_executions_count=stats.tool_executions_count,
        agent_runs_count=stats.agent_runs_count,
        task_executions_count=stats.task_executions_count,
        permission_denials_count=stats.permission_denials_count,
        security_events_count=stats.security_events_count,
        evaluation_runs_count=stats.evaluation_runs_count,
        automation_runs_count=stats.automation_runs_count,
        integration_failures_count=stats.integration_failures_count,
    )
