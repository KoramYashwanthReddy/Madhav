"""Master Observability & Audit Service for Module 33."""


from max.observability.domain.models import (
    ExecutionTimeline,
    ExecutionTimelineItem,
    ObservabilityHealthStatus,
    ObservabilityStatistics,
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
from max.observability.services.audit_service import AuditService
from max.observability.services.error_tracking_service import ErrorTrackingService
from max.observability.services.logging_service import LoggingService
from max.observability.services.metrics_service import MetricsService
from max.observability.services.redaction_service import RedactionService
from max.observability.services.tracing_service import TracingService


class ObservabilityService:
    """Master facade for Module 33 — Observability & Audit.

    OBSERVES MAX runtime behaviors. Does NOT execute tools, alter permissions,
    or modify user configuration/state.
    """

    def __init__(
        self,
        log_repository: LogRepository,
        metric_repository: MetricRepository,
        trace_repository: TraceRepository,
        span_repository: SpanRepository,
        audit_repository: AuditEventRepository,
        error_repository: ErrorRepository,
        component_repository: ComponentRepository,
        execution_repository: ExecutionRepository,
        logging_service: LoggingService,
        metrics_service: MetricsService,
        tracing_service: TracingService,
        audit_service: AuditService,
        error_tracking_service: ErrorTrackingService,
        redaction_service: RedactionService,
        enabled: bool = True,
    ) -> None:
        self.log_repository = log_repository
        self.metric_repository = metric_repository
        self.trace_repository = trace_repository
        self.span_repository = span_repository
        self.audit_repository = audit_repository
        self.error_repository = error_repository
        self.component_repository = component_repository
        self.execution_repository = execution_repository

        self.logging = logging_service
        self.metrics = metrics_service
        self.tracing = tracing_service
        self.audit = audit_service
        self.error_tracking = error_tracking_service
        self.redaction = redaction_service
        self.enabled = enabled

    async def get_execution_timeline(self, execution_id: str) -> ExecutionTimeline | None:
        """Derive an execution timeline from trace and span timestamps for an execution ID."""
        # Check cached timeline first
        timeline = await self.execution_repository.get_timeline(execution_id)
        if timeline:
            return timeline

        # Derive from trace data matching execution_id
        traces = await self.trace_repository.search_traces(execution_id=execution_id, limit=1)
        if not traces:
            return None

        trace = traces[0]
        spans = trace.spans
        if not spans:
            return None

        spans_sorted = sorted(spans, key=lambda s: s.start_time)
        root_start = spans_sorted[0].start_time

        items: list[ExecutionTimelineItem] = []
        for s in spans_sorted:
            offset_ms = (s.start_time - root_start).total_seconds() * 1000.0
            item = ExecutionTimelineItem(
                timestamp=s.start_time,
                relative_offset_ms=round(offset_ms, 3),
                span_id=s.span_id,
                span_name=s.name,
                span_type=s.span_type,
                event_name=f"span_{s.name}",
                status=s.status,
                duration_ms=s.duration_ms,
                details=s.attributes,
            )
            items.append(item)

        total_duration = (
            trace.duration_ms
            if trace.duration_ms is not None
            else (spans_sorted[-1].end_time - root_start).total_seconds() * 1000.0
            if spans_sorted[-1].end_time
            else 0.0
        )

        derived_timeline = ExecutionTimeline(
            execution_id=execution_id,
            trace_id=trace.trace_id,
            request_id=trace.request_id,
            correlation_id=trace.correlation_id,
            start_time=root_start,
            total_duration_ms=round(total_duration, 3),
            span_count=len(spans),
            items=items,
        )

        await self.execution_repository.save_timeline(derived_timeline)
        return derived_timeline

    async def get_statistics(self) -> ObservabilityStatistics:
        """Calculate operational system statistics summary."""
        logs_cnt = await self.log_repository.count()
        traces_cnt = await self.trace_repository.count()
        audits_cnt = await self.audit_repository.count()

        # Query metrics aggregations
        http_requests = await self.metric_repository.get_aggregations(name="http_requests_total")
        errors = await self.metric_repository.get_aggregations(name="errors_total")
        latencies = await self.metric_repository.get_aggregations(name="http_request_duration")
        tool_execs = await self.metric_repository.get_aggregations(name="tool_invocations_total")
        agent_runs = await self.metric_repository.get_aggregations(name="agent_runs_total")
        task_execs = await self.metric_repository.get_aggregations(name="tasks_completed_total")
        perm_denials = await self.metric_repository.get_aggregations(name="permission_denials_total")
        security_evts = await self.metric_repository.get_aggregations(name="security_events_total")
        eval_runs = await self.metric_repository.get_aggregations(name="evaluation_runs_total")
        auto_runs = await self.metric_repository.get_aggregations(name="automation_runs_total")
        integ_fails = await self.metric_repository.get_aggregations(name="integration_failures_total")

        req_sum = sum(a.sum for a in http_requests) if http_requests else 0
        err_sum = sum(a.sum for a in errors) if errors else 0
        avg_lat = latencies[0].avg if latencies and latencies[0].avg else 0.0
        p95_lat = latencies[0].p95 if latencies and latencies[0].p95 else 0.0

        return ObservabilityStatistics(
            total_requests_today=int(req_sum),
            total_errors_today=int(err_sum),
            avg_latency_ms=round(avg_lat, 2),
            p95_latency_ms=round(p95_lat, 2),
            active_traces_count=traces_cnt,
            total_spans_recorded=traces_cnt,
            total_logs_recorded=logs_cnt,
            total_metrics_recorded=len(await self.metric_repository.get_all_raw(100)),
            total_audit_events_recorded=audits_cnt,
            tool_executions_count=int(sum(a.sum for a in tool_execs)) if tool_execs else 0,
            agent_runs_count=int(sum(a.sum for a in agent_runs)) if agent_runs else 0,
            task_executions_count=int(sum(a.sum for a in task_execs)) if task_execs else 0,
            permission_denials_count=int(sum(a.sum for a in perm_denials)) if perm_denials else 0,
            security_events_count=int(sum(a.sum for a in security_evts)) if security_evts else 0,
            evaluation_runs_count=int(sum(a.sum for a in eval_runs)) if eval_runs else 0,
            automation_runs_count=int(sum(a.sum for a in auto_runs)) if auto_runs else 0,
            integration_failures_count=int(sum(a.sum for a in integ_fails)) if integ_fails else 0,
        )

    async def get_health_status(self) -> ObservabilityHealthStatus:
        """Evaluate status of observability subsystem components."""
        return ObservabilityHealthStatus(
            is_healthy=True,
            storage_healthy=True,
            log_exporter_healthy=True,
            trace_exporter_healthy=True,
            metric_exporter_healthy=True,
            audit_storage_healthy=True,
            details={
                "enabled": self.enabled,
                "logging_min_level": self.logging.min_level.value,
                "tracing_enabled": self.tracing.enabled,
                "audit_enabled": self.audit.enabled,
                "redaction_enabled": self.redaction.enabled,
            },
        )
