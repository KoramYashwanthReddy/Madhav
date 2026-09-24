"""Distributed tracing service for Module 33 — Observability & Audit."""

import random
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from max.observability.domain.enums import (
    SamplingStrategy,
    SpanKind,
    SpanStatus,
    SpanType,
)
from max.observability.domain.models import (
    Span,
    SpanEvent,
    Trace,
    generate_uuid,
    now_utc,
)
from max.observability.exporters.base import TelemetryExporter
from max.observability.repositories.interfaces import SpanRepository, TraceRepository
from max.observability.services.correlation_service import CorrelationService
from max.observability.services.redaction_service import RedactionService


class TracingService:
    """Manages distributed traces, nested spans, context propagation, and sampling."""

    def __init__(
        self,
        trace_repository: TraceRepository,
        span_repository: SpanRepository,
        exporter: TelemetryExporter | None = None,
        redaction_service: RedactionService | None = None,
        sampling_strategy: SamplingStrategy = SamplingStrategy.ALWAYS_ON,
        sample_rate: float = 1.0,
        enabled: bool = True,
        max_attribute_size_bytes: int = 4096,
    ) -> None:
        self.trace_repository = trace_repository
        self.span_repository = span_repository
        self.exporter = exporter
        self.redaction_service = redaction_service or RedactionService()
        self.sampling_strategy = sampling_strategy
        self.sample_rate = sample_rate
        self.enabled = enabled
        self.max_attribute_size_bytes = max_attribute_size_bytes

    def should_sample(self, is_error: bool = False) -> bool:
        """Evaluate sampling policy for a trace execution."""
        if not self.enabled or self.sampling_strategy == SamplingStrategy.ALWAYS_OFF:
            return False
        if self.sampling_strategy == SamplingStrategy.ALWAYS_ON:
            return True
        if self.sampling_strategy == SamplingStrategy.ERROR_ONLY:
            return is_error
        if self.sampling_strategy in (SamplingStrategy.PROBABILISTIC, SamplingStrategy.CONFIGURABLE):
            return random.random() < self.sample_rate
        return True

    def _sanitize_attributes(self, attrs: dict[str, Any] | None) -> dict[str, Any]:
        """Redact and clamp attribute payload sizes to protect high-cardinality limits."""
        if not attrs:
            return {}

        clean = self.redaction_service.redact_dict(attrs)
        sanitized: dict[str, Any] = {}

        for k, v in clean.items():
            str_v = str(v)
            if len(str_v.encode("utf-8")) > self.max_attribute_size_bytes:
                sanitized[k] = str_v[: self.max_attribute_size_bytes] + "...[TRUNCATED]"
            else:
                sanitized[k] = v

        return sanitized

    async def start_trace(
        self,
        name: str,
        span_type: SpanType = SpanType.HTTP_REQUEST,
        request_id: str | None = None,
        correlation_id: str | None = None,
        execution_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> tuple[Trace, Span]:
        """Initialize a new trace and root span."""
        ctx = CorrelationService.get_current_context()
        trace_id = generate_uuid()
        root_span_id = generate_uuid()

        ctx.trace_id = trace_id
        ctx.span_id = root_span_id
        if request_id:
            ctx.request_id = request_id
        if correlation_id:
            ctx.correlation_id = correlation_id
        if execution_id:
            ctx.execution_id = execution_id

        root_span = Span(
            span_id=root_span_id,
            trace_id=trace_id,
            parent_span_id=None,
            span_type=span_type,
            name=name,
            span_kind=SpanKind.SERVER if span_type == SpanType.HTTP_REQUEST else SpanKind.INTERNAL,
            start_time=now_utc(),
            status=SpanStatus.UNSET,
            attributes=self._sanitize_attributes(attributes),
        )

        trace = Trace(
            trace_id=trace_id,
            root_span_id=root_span_id,
            request_id=ctx.request_id,
            correlation_id=ctx.correlation_id,
            execution_id=ctx.execution_id,
            start_time=root_span.start_time,
            status=SpanStatus.UNSET,
            span_count=1,
            spans=[root_span],
        )

        if self.enabled:
            await self.span_repository.save_span(root_span)
            await self.trace_repository.save_trace(trace)

        return trace, root_span

    async def start_span(
        self,
        name: str,
        span_type: SpanType = SpanType.CUSTOM,
        parent_span_id: str | None = None,
        span_kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a child span attached to the current active trace."""
        ctx = CorrelationService.get_current_context()
        parent_id = parent_span_id or ctx.span_id

        span = Span(
            span_id=generate_uuid(),
            trace_id=ctx.trace_id,
            parent_span_id=parent_id,
            span_type=span_type,
            name=name,
            span_kind=span_kind,
            start_time=now_utc(),
            status=SpanStatus.UNSET,
            attributes=self._sanitize_attributes(attributes),
        )

        ctx.span_id = span.span_id

        if self.enabled:
            await self.span_repository.save_span(span)
            trace = await self.trace_repository.get_trace(ctx.trace_id)
            if trace:
                trace.spans.append(span)
                trace.span_count = len(trace.spans)
                await self.trace_repository.save_trace(trace)

        return span

    async def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.OK,
        status_message: str | None = None,
    ) -> Span:
        """Mark span completion, compute duration, and save."""
        span = await self.span_repository.get_span(span_id)
        if not span:
            # Fallback if span wasn't saved or found
            span = Span(
                span_id=span_id,
                trace_id="unknown",
                name="unknown",
                start_time=now_utc(),
            )

        end_t = now_utc()
        span.end_time = end_t
        span.duration_ms = (end_t - span.start_time).total_seconds() * 1000.0
        span.status = status
        if status_message:
            span.status_message = self.redaction_service.redact_text(status_message)

        if self.enabled:
            await self.span_repository.save_span(span)

            # If this is the root span or trace is complete, update trace summary
            trace = await self.trace_repository.get_trace(span.trace_id)
            if trace:
                if trace.root_span_id == span.span_id:
                    trace.end_time = end_t
                    trace.duration_ms = (end_t - trace.start_time).total_seconds() * 1000.0
                    trace.status = status

                if status == SpanStatus.ERROR:
                    trace.error_count += 1
                    trace.status = SpanStatus.ERROR

                await self.trace_repository.save_trace(trace)

                if trace.root_span_id == span.span_id and self.exporter:
                    if self.should_sample(is_error=(trace.status == SpanStatus.ERROR)):
                        try:
                            await self.exporter.export_trace(trace)
                        except Exception:
                            pass

        return span

    async def add_span_event(self, span_id: str, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event record to an active span."""
        span = await self.span_repository.get_span(span_id)
        if span:
            event = SpanEvent(
                timestamp=now_utc(),
                name=name,
                attributes=self._sanitize_attributes(attributes),
            )
            span.events.append(event)
            await self.span_repository.save_span(span)

    async def add_span_attribute(self, span_id: str, key: str, value: Any) -> None:
        """Add or update an attribute on a span."""
        span = await self.span_repository.get_span(span_id)
        if span:
            clean_val = self._sanitize_attributes({key: value}).get(key)
            span.attributes[key] = clean_val
            await self.span_repository.save_span(span)

    async def record_span_exception(self, span_id: str, exception: Exception) -> None:
        """Attach exception metadata to a span and mark its status as ERROR."""
        span = await self.span_repository.get_span(span_id)
        if span:
            span.status = SpanStatus.ERROR
            span.status_message = str(exception)
            event = SpanEvent(
                timestamp=now_utc(),
                name="exception",
                attributes={
                    "exception.type": type(exception).__name__,
                    "exception.message": self.redaction_service.redact_text(str(exception)),
                },
            )
            span.events.append(event)
            await self.span_repository.save_span(span)

    @asynccontextmanager
    async def trace_block(
        self,
        name: str,
        span_type: SpanType = SpanType.CUSTOM,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncGenerator[Span, None]:
        """Async context manager wrapper for creating and auto-ending spans."""
        span = await self.start_span(name, span_type=span_type, attributes=attributes)
        try:
            yield span
            await self.end_span(span.span_id, status=SpanStatus.OK)
        except Exception as exc:
            await self.record_span_exception(span.span_id, exc)
            await self.end_span(span.span_id, status=SpanStatus.ERROR, status_message=str(exc))
            raise
