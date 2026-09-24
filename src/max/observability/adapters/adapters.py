"""Module adapters for recording spans, metrics, logs, and audit events across Modules 01-32."""


from max.observability.domain.enums import (
    AuditActor,
    AuditCategory,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
)
from max.observability.services.observability_service import ObservabilityService


class ObservabilityAdapter:
    """Helper adapter providing convenience wrappers for modules across MAX to emit observability signals."""

    def __init__(self, observability_service: ObservabilityService) -> None:
        self.obs = observability_service

    async def record_http_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        request_id: str | None = None,
    ) -> None:
        """Record HTTP request metrics and span summary."""
        await self.obs.metrics.counter_increment(
            "http_requests_total",
            labels={"method": method, "status_code": str(status_code)},
        )
        await self.obs.metrics.timer_record(
            "http_request_duration",
            duration_ms,
            labels={"method": method, "status_code": str(status_code)},
        )
        if status_code >= 400:
            await self.obs.metrics.counter_increment(
                "http_request_errors_total",
                labels={"method": method, "status_code": str(status_code)},
            )

    async def record_model_inference(
        self,
        model_id: str,
        provider: str,
        latency_ms: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        is_error: bool = False,
    ) -> None:
        """Record Module 04 AI Runtime model inference metrics."""
        await self.obs.metrics.counter_increment(
            "model_requests_total", labels={"provider": provider}
        )
        await self.obs.metrics.timer_record(
            "model_latency", latency_ms, labels={"provider": provider}
        )
        if prompt_tokens > 0:
            await self.obs.metrics.counter_increment(
                "model_tokens_input", value=float(prompt_tokens), labels={"provider": provider}
            )
        if completion_tokens > 0:
            await self.obs.metrics.counter_increment(
                "model_tokens_output", value=float(completion_tokens), labels={"provider": provider}
            )
        if is_error:
            await self.obs.metrics.counter_increment(
                "model_errors_total", labels={"provider": provider}
            )

    async def record_tool_invocation(
        self,
        tool_name: str,
        tool_category: str,
        duration_ms: float,
        success: bool = True,
        permission_denied: bool = False,
    ) -> None:
        """Record Module 14 Tool invocation metrics and traces."""
        await self.obs.metrics.counter_increment(
            "tool_invocations_total", labels={"tool_category": tool_category}
        )
        await self.obs.metrics.timer_record(
            "tool_duration", duration_ms, labels={"tool_category": tool_category}
        )
        if not success:
            await self.obs.metrics.counter_increment(
                "tool_failures_total", labels={"tool_category": tool_category}
            )
        if permission_denied:
            await self.obs.metrics.counter_increment(
                "tool_permission_denials_total", labels={"tool_category": tool_category}
            )

    async def record_permission_check(
        self,
        actor_id: str,
        resource: str,
        action: str,
        decision: str,  # ALLOW, DENY, REQUIRE_APPROVAL
        reason: str | None = None,
    ) -> None:
        """Record Module 15 Security permission decision in metrics and append-only audit log."""
        outcome = (
            AuditOutcome.SUCCESS
            if decision == "ALLOW"
            else AuditOutcome.DENIED
            if decision == "DENY"
            else AuditOutcome.REQUIRES_APPROVAL
        )
        severity = AuditSeverity.INFO if decision == "ALLOW" else AuditSeverity.HIGH

        await self.obs.metrics.counter_increment(
            "permission_checks_total", labels={"outcome": decision.lower()}
        )
        if decision == "DENY":
            await self.obs.metrics.counter_increment("permission_denials_total")
        elif decision == "REQUIRE_APPROVAL":
            await self.obs.metrics.counter_increment("approval_requests_total")

        await self.obs.audit.record(
            event_type=AuditEventType.PERMISSION,
            actor=AuditActor.AGENT if "agent" in actor_id.lower() else AuditActor.USER,
            actor_id=actor_id,
            action=action,
            target=resource,
            outcome=outcome,
            severity=severity,
            category=AuditCategory.SECURITY,
            reason=reason,
            details={"decision": decision, "resource": resource},
        )

    async def record_task_lifecycle(
        self, task_id: str, status: str, duration_ms: float | None = None
    ) -> None:
        """Record Module 12 Task lifecycle execution metrics."""
        await self.obs.metrics.counter_increment("tasks_created_total")
        if status == "COMPLETED":
            await self.obs.metrics.counter_increment("tasks_completed_total")
            if duration_ms is not None:
                await self.obs.metrics.timer_record("task_duration", duration_ms)
        elif status == "FAILED":
            await self.obs.metrics.counter_increment("tasks_failed_total")

    async def record_agent_run(
        self, agent_id: str, agent_type: str, duration_ms: float, success: bool = True
    ) -> None:
        """Record Module 13 Agent execution run metrics."""
        await self.obs.metrics.counter_increment(
            "agent_runs_total", labels={"agent_type": agent_type}
        )
        await self.obs.metrics.timer_record(
            "agent_duration", duration_ms, labels={"agent_type": agent_type}
        )
        if not success:
            await self.obs.metrics.counter_increment(
                "agent_failures_total", labels={"agent_type": agent_type}
            )

    async def record_rag_retrieval(
        self, duration_ms: float, results_count: int, query_length: int = 0
    ) -> None:
        """Record Module 10 RAG & Retrieval operation metrics."""
        await self.obs.metrics.counter_increment("retrieval_requests_total")
        await self.obs.metrics.timer_record("retrieval_latency", duration_ms)
        await self.obs.metrics.histogram_observe(
            "retrieval_results", float(results_count), unit="1"
        )

    async def record_evaluation_run(
        self, eval_type: str, duration_ms: float, passed: bool = True
    ) -> None:
        """Record Module 32 Evaluation run execution metrics."""
        await self.obs.metrics.counter_increment(
            "evaluation_runs_total", labels={"evaluation_type": eval_type}
        )
        if not passed:
            await self.obs.metrics.counter_increment(
                "evaluation_failures_total", labels={"evaluation_type": eval_type}
            )

    async def record_security_event(
        self, event_type: str, description: str, severity: AuditSeverity = AuditSeverity.HIGH
    ) -> None:
        """Record Module 15 security event or policy violation."""
        await self.obs.metrics.counter_increment("security_events_total")
        if severity in (AuditSeverity.HIGH, AuditSeverity.CRITICAL):
            await self.obs.metrics.counter_increment("security_violations_total")

        await self.obs.audit.record(
            event_type=AuditEventType.SECURITY,
            actor=AuditActor.SYSTEM,
            action=event_type,
            target="security_subsystem",
            outcome=AuditOutcome.FAILURE if severity == AuditSeverity.CRITICAL else AuditOutcome.SUCCESS,
            severity=severity,
            category=AuditCategory.SECURITY,
            reason=description,
        )
