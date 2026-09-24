"""Exceptions for Module 33 — Observability & Audit."""

from typing import Any


class ObservabilityError(Exception):
    """Base exception for observability and audit errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TraceNotFoundError(ObservabilityError):
    """Raised when a requested trace ID is not found."""

    pass


class SpanNotFoundError(ObservabilityError):
    """Raised when a requested span ID is not found."""

    pass


class AuditEventNotFoundError(ObservabilityError):
    """Raised when a requested audit event ID is not found."""

    pass


class RedactionError(ObservabilityError):
    """Raised when a redaction operation encounters an unrecoverable failure."""

    pass


class AuditImmutabilityError(ObservabilityError):
    """Raised when an illegal modification or deletion of append-only audit events is attempted."""

    pass


class TelemetryExportError(ObservabilityError):
    """Raised when telemetry export fails critically."""

    pass


class OversizedPayloadError(ObservabilityError):
    """Raised when an telemetry payload exceeds high-cardinality size limits."""

    pass
