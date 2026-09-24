"""Correlation and context propagation service using Python contextvars for Module 33."""

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

from max.observability.domain.models import ObservabilityContext, generate_uuid

# Task-isolated contextvar for carrying observability correlation identifiers
_OBSERVABILITY_CONTEXT: ContextVar[ObservabilityContext | None] = ContextVar(
    "observability_context", default=None
)


class CorrelationService:
    """Manages request, correlation, trace, span, and execution ID context propagation."""

    @staticmethod
    def get_current_context() -> ObservabilityContext:
        """Get the current observability context or create a default root context."""
        ctx = _OBSERVABILITY_CONTEXT.get()
        if ctx is None:
            ctx = ObservabilityContext()
            _OBSERVABILITY_CONTEXT.set(ctx)
        return ctx

    @staticmethod
    def set_current_context(context: ObservabilityContext) -> None:
        """Set the active observability context for the current task/thread."""
        _OBSERVABILITY_CONTEXT.set(context)

    @staticmethod
    def reset_context() -> None:
        """Reset the active context to None."""
        _OBSERVABILITY_CONTEXT.set(None)

    @staticmethod
    def ensure_request_id(incoming_request_id: str | None = None) -> str:
        """Validate or generate a safe request ID for an incoming HTTP/API call."""
        if incoming_request_id and incoming_request_id.strip():
            safe_id = incoming_request_id.strip()[:64]
            ctx = CorrelationService.get_current_context()
            ctx.request_id = safe_id
            return safe_id

        ctx = CorrelationService.get_current_context()
        return ctx.request_id

    @staticmethod
    def ensure_correlation_id(incoming_correlation_id: str | None = None) -> str:
        """Validate or generate a correlation ID across component boundaries."""
        if incoming_correlation_id and incoming_correlation_id.strip():
            safe_id = incoming_correlation_id.strip()[:64]
            ctx = CorrelationService.get_current_context()
            ctx.correlation_id = safe_id
            return safe_id

        ctx = CorrelationService.get_current_context()
        return ctx.correlation_id

    @staticmethod
    @contextmanager
    def scope_context(
        request_id: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        execution_id: str | None = None,
        component: str | None = None,
        operation: str | None = None,
    ) -> Generator[ObservabilityContext, None, None]:
        """Scope a child or isolated context for a block of code, restoring prior context upon exit."""
        parent = CorrelationService.get_current_context()

        child = ObservabilityContext(
            request_id=request_id or parent.request_id,
            correlation_id=correlation_id or parent.correlation_id,
            trace_id=trace_id or parent.trace_id,
            span_id=span_id or generate_uuid(),
            execution_id=execution_id or parent.execution_id,
            user_id=parent.user_id,
            component=component or parent.component,
            operation=operation or parent.operation,
            environment=parent.environment,
            version=parent.version,
        )

        token = _OBSERVABILITY_CONTEXT.set(child)
        try:
            yield child
        finally:
            _OBSERVABILITY_CONTEXT.reset(token)
