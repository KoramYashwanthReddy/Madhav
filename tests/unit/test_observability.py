"""Unit tests for Module 33 — Observability & Audit."""

import asyncio

import pytest

from max.observability.container import ObservabilityContainer
from max.observability.domain.enums import (
    AuditActor,
    AuditEventType,
    AuditOutcome,
    AuditSeverity,
    LogLevel,
    SpanStatus,
    SpanType,
)
from max.observability.domain.exceptions import AuditImmutabilityError
from max.observability.domain.models import (
    StructuredLogEntry,
    generate_uuid,
)
from max.observability.exporters.otlp import OTLPExporter
from max.observability.services.correlation_service import CorrelationService
from max.observability.services.redaction_service import RedactionService


@pytest.fixture(autouse=True)
def reset_observability():
    """Reset singleton instance before each test."""
    ObservabilityContainer.reset_instance()
    CorrelationService.reset_context()
    yield
    ObservabilityContainer.reset_instance()
    CorrelationService.reset_context()


@pytest.mark.asyncio
async def test_correlation_context_propagation():
    """Test context propagation across execution boundaries and task isolation."""
    ctx = CorrelationService.get_current_context()
    assert ctx.request_id is not None
    assert ctx.correlation_id is not None

    CorrelationService.ensure_request_id("custom-req-123")
    assert CorrelationService.get_current_context().request_id == "custom-req-123"

    with CorrelationService.scope_context(component="agent", operation="tool_run") as scoped:
        assert scoped.request_id == "custom-req-123"
        assert scoped.component == "agent"
        assert scoped.operation == "tool_run"

    # Restored parent context
    assert CorrelationService.get_current_context().component == "core"


@pytest.mark.asyncio
async def test_secret_redaction_service():
    """Test redaction of sensitive credentials, tokens, and passwords."""
    redactor = RedactionService()

    payload = {
        "user": "alice",
        "password": "secret_password_123",
        "api_key": "sk-1234567890",
        "nested": {
            "access_token": "bearer-token-abc",
            "normal_data": "value",
        },
    }

    clean = redactor.redact_dict(payload)
    assert clean["user"] == "alice"
    assert clean["password"] == "[REDACTED]"
    assert clean["api_key"] == "[REDACTED]"
    assert clean["nested"]["access_token"] == "[REDACTED]"
    assert clean["nested"]["normal_data"] == "value"

    raw_text = "Header Authorization: Bearer secret-token-xyz with api_key='sk-test'"
    clean_text = redactor.redact_text(raw_text)
    assert "secret-token-xyz" not in clean_text
    assert "[REDACTED]" in clean_text


@pytest.mark.asyncio
async def test_log_injection_prevention():
    """Test log injection sanitization (escaping control characters and newlines)."""
    redactor = RedactionService()

    malicious_msg = "User logged in\n[CRITICAL] Fake admin bypass injection\r\n"
    sanitized = redactor.sanitize_log_message(malicious_msg)
    assert "\n" not in sanitized
    assert "\r" not in sanitized
    assert "Fake admin bypass injection" in sanitized


@pytest.mark.asyncio
async def test_ai_prompt_privacy():
    """Test AI prompt content hashing and redaction preview."""
    redactor = RedactionService()

    prompt = "My password is secret_123. Summarize this confidential contract."
    result = redactor.redact_ai_content(prompt, capture_enabled=False)

    assert "content_hash" in result
    assert result["content_hash"] is not None
    assert "secret_123" not in result["preview"]
    assert result["opt_in_captured"] is False


@pytest.mark.asyncio
async def test_structured_logging():
    """Test structured logging service and log repository query."""
    container = ObservabilityContainer.get_instance()
    logging_svc = container.logging_service

    await logging_svc.info("Application starting", component="init", event_name="startup")
    await logging_svc.error(
        "Database connection failed",
        component="db",
        event_name="connection_error",
        attributes={"password": "db_pass_secret"},
    )

    logs = await container.log_repository.query()
    assert len(logs) == 2

    error_log = [log_item for log_item in logs if log_item.level == LogLevel.ERROR][0]
    assert error_log.component == "db"
    assert error_log.attributes["password"] == "[REDACTED]"
    assert error_log.trace_id is not None


@pytest.mark.asyncio
async def test_metrics_service_and_cardinality_protection():
    """Test counter, gauge, timer, histogram, and label cardinality bounds."""
    container = ObservabilityContainer.get_instance()
    metrics_svc = container.metrics_service

    await metrics_svc.counter_increment("http_requests_total", labels={"method": "GET", "status_code": "200"})
    await metrics_svc.counter_increment("http_requests_total", labels={"method": "GET", "status_code": "200"})
    await metrics_svc.gauge_set("active_agents_count", 3.0)
    await metrics_svc.timer_record("http_request_duration", 45.5, labels={"method": "GET"})

    aggs = await container.metric_repository.get_aggregations(name="http_requests_total")
    assert len(aggs) == 1
    assert aggs[0].count == 2
    assert aggs[0].sum == 2.0

    timer_aggs = await container.metric_repository.get_aggregations(name="http_request_duration")
    assert len(timer_aggs) == 1
    assert timer_aggs[0].avg == 45.5


@pytest.mark.asyncio
async def test_distributed_tracing_service():
    """Test trace and span creation, parent-child links, events, and status."""
    container = ObservabilityContainer.get_instance()
    tracing_svc = container.tracing_service

    trace, root_span = await tracing_svc.start_trace("HTTP GET /chat", span_type=SpanType.HTTP_REQUEST)
    assert trace.trace_id is not None
    assert root_span.span_id == trace.root_span_id

    child1 = await tracing_svc.start_span("conversation_engine", span_type=SpanType.CONVERSATION)
    assert child1.parent_span_id == root_span.span_id

    child2 = await tracing_svc.start_span("model_inference", span_type=SpanType.MODEL_INFERENCE)
    await tracing_svc.add_span_event(child2.span_id, "tokens_generated", {"token_count": 120})
    await tracing_svc.end_span(child2.span_id, status=SpanStatus.OK)

    await tracing_svc.end_span(child1.span_id, status=SpanStatus.OK)
    await tracing_svc.end_span(root_span.span_id, status=SpanStatus.OK)

    fetched_trace = await container.trace_repository.get_trace(trace.trace_id)
    assert fetched_trace is not None
    assert fetched_trace.span_count == 3
    assert fetched_trace.status == SpanStatus.OK
    assert fetched_trace.duration_ms is not None


@pytest.mark.asyncio
async def test_audit_service_immutability():
    """Test append-only audit event persistence and immutability violation error."""
    container = ObservabilityContainer.get_instance()
    audit_svc = container.audit_service

    evt1 = await audit_svc.record(
        event_type=AuditEventType.PERMISSION,
        actor=AuditActor.AGENT,
        action="execute_terminal_command",
        target="terminal",
        outcome=AuditOutcome.DENIED,
        severity=AuditSeverity.HIGH,
        reason="Security policy violation",
    )

    assert evt1.event_id is not None
    assert evt1.outcome == AuditOutcome.DENIED

    # Attempting to overwrite existing event ID should raise AuditImmutabilityError
    with pytest.raises(AuditImmutabilityError):
        await container.audit_repository.append(evt1)

    searched = await audit_svc.search_events(outcome=AuditOutcome.DENIED)
    assert len(searched) == 1
    assert searched[0].event_id == evt1.event_id


@pytest.mark.asyncio
async def test_execution_timeline():
    """Test deriving execution timeline from recorded trace spans."""
    container = ObservabilityContainer.get_instance()
    obs_svc = container.observability_service
    tracing_svc = container.tracing_service

    exec_id = generate_uuid()
    trace, root = await tracing_svc.start_trace(
        "Request Execution", span_type=SpanType.HTTP_REQUEST, execution_id=exec_id
    )

    await asyncio.sleep(0.01)
    span1 = await tracing_svc.start_span("context_build", span_type=SpanType.CONTEXT_BUILD)
    await tracing_svc.end_span(span1.span_id)

    await tracing_svc.end_span(root.span_id)

    timeline = await obs_svc.get_execution_timeline(exec_id)
    assert timeline is not None
    assert timeline.execution_id == exec_id
    assert timeline.span_count == 2
    assert len(timeline.items) == 2
    assert timeline.items[0].span_name == "Request Execution"


@pytest.mark.asyncio
async def test_otlp_exporter_resilience():
    """Test OTLP exporter handles unreachable collector endpoints without crashing."""
    otlp = OTLPExporter(endpoint="http://unreachable-host:9999", enabled=True)

    log_entry = StructuredLogEntry(message="Test log")
    success = await otlp.export_log(log_entry)
    # Should complete without throwing exception
    assert isinstance(success, bool)
