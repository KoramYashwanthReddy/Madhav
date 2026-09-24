"""Integration tests for Module 33 Observability & Audit REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from max.main import app
from max.observability.container import ObservabilityContainer
from max.observability.domain.enums import (
    AuditActor,
    AuditEventType,
    AuditOutcome,
    SpanStatus,
    SpanType,
)
from max.observability.services.correlation_service import CorrelationService


@pytest.fixture(autouse=True)
def setup_container():
    """Reset container and seed test data before each test."""
    ObservabilityContainer.reset_instance()
    CorrelationService.reset_context()
    yield
    ObservabilityContainer.reset_instance()
    CorrelationService.reset_context()


@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Test GET /api/v1/observability/health."""
    client = TestClient(app)
    res = client.get("/api/v1/observability/health")
    assert res.status_code == 200
    body = res.json()
    assert body["is_healthy"] is True
    assert body["storage_healthy"] is True


@pytest.mark.asyncio
async def test_api_logs_endpoint():
    """Test GET /api/v1/observability/logs."""
    container = ObservabilityContainer.get_instance()
    await container.logging_service.info("Test message", component="test_comp")

    client = TestClient(app)
    res = client.get("/api/v1/observability/logs")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert any(item["message"] == "Test message" for item in body["items"])


@pytest.mark.asyncio
async def test_api_metrics_endpoint():
    """Test GET /api/v1/observability/metrics."""
    container = ObservabilityContainer.get_instance()
    await container.metrics_service.counter_increment("http_requests_total", labels={"method": "GET"})

    client = TestClient(app)
    res = client.get("/api/v1/observability/metrics?name=http_requests_total")
    assert res.status_code == 200
    body = res.json()
    assert len(body["aggregations"]) >= 1
    assert body["aggregations"][0]["name"] == "http_requests_total"


@pytest.mark.asyncio
async def test_api_traces_endpoints():
    """Test GET /api/v1/observability/traces and GET /api/v1/observability/traces/{trace_id}."""
    container = ObservabilityContainer.get_instance()
    trace, span = await container.tracing_service.start_trace("API Test Trace", span_type=SpanType.HTTP_REQUEST)
    await container.tracing_service.end_span(span.span_id, status=SpanStatus.OK)

    client = TestClient(app)

    # Search traces
    res = client.get("/api/v1/observability/traces")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1

    # Get trace detail
    res_detail = client.get(f"/api/v1/observability/traces/{trace.trace_id}")
    assert res_detail.status_code == 200
    detail_body = res_detail.json()
    assert detail_body["trace_id"] == trace.trace_id
    assert len(detail_body["spans"]) >= 1


@pytest.mark.asyncio
async def test_api_audit_endpoints():
    """Test GET /api/v1/observability/audit and GET /api/v1/observability/audit/{event_id}."""
    container = ObservabilityContainer.get_instance()
    event = await container.audit_service.record(
        event_type=AuditEventType.PERMISSION,
        actor=AuditActor.USER,
        action="connect_integration",
        target="github",
        outcome=AuditOutcome.SUCCESS,
    )

    client = TestClient(app)

    # Search audit records
    res = client.get("/api/v1/observability/audit")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1

    # Get single audit event detail
    res_detail = client.get(f"/api/v1/observability/audit/{event.event_id}")
    assert res_detail.status_code == 200
    detail_body = res_detail.json()
    assert detail_body["event_id"] == event.event_id
    assert detail_body["target"] == "github"


@pytest.mark.asyncio
async def test_api_statistics_endpoint():
    """Test GET /api/v1/observability/statistics."""
    client = TestClient(app)
    res = client.get("/api/v1/observability/statistics")
    assert res.status_code == 200
    body = res.json()
    assert "total_requests_today" in body
    assert "total_logs_recorded" in body
    assert "total_audit_events_recorded" in body


@pytest.mark.asyncio
async def test_api_components_and_errors_endpoints():
    """Test GET /api/v1/observability/components and GET /api/v1/observability/errors."""
    container = ObservabilityContainer.get_instance()
    await container.error_tracking_service.record_exception(
        ValueError("Sample test exception"), component="test_comp"
    )

    client = TestClient(app)

    res_comp = client.get("/api/v1/observability/components")
    assert res_comp.status_code == 200

    res_err = client.get("/api/v1/observability/errors")
    assert res_err.status_code == 200
    body_err = res_err.json()
    assert len(body_err["items"]) >= 1
    assert body_err["items"][0]["error_type"] == "ValueError"
