"""Dependency container for Module 33 — Observability & Audit."""

from max.config.settings import Settings
from max.observability.adapters.adapters import ObservabilityAdapter
from max.observability.domain.enums import (
    LogLevel,
    SamplingStrategy,
)
from max.observability.exporters.base import TelemetryExporter
from max.observability.exporters.in_memory import InMemoryExporter
from max.observability.exporters.otlp import OTLPExporter
from max.observability.repositories.repositories import (
    InMemoryAuditEventRepository,
    InMemoryComponentRepository,
    InMemoryErrorRepository,
    InMemoryExecutionRepository,
    InMemoryLogRepository,
    InMemoryMetricRepository,
    InMemorySpanRepository,
    InMemoryTraceRepository,
)
from max.observability.services.audit_service import AuditService
from max.observability.services.error_tracking_service import ErrorTrackingService
from max.observability.services.logging_service import LoggingService
from max.observability.services.metrics_service import MetricsService
from max.observability.services.observability_service import ObservabilityService
from max.observability.services.redaction_service import RedactionService
from max.observability.services.tracing_service import TracingService


class ObservabilityContainer:
    """Dependency container managing lifetime of Observability components."""

    _instance: "ObservabilityContainer | None" = None

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        obs_cfg = self.settings.observability

        # Repositories
        self.log_repository = InMemoryLogRepository(max_capacity=10000)
        self.metric_repository = InMemoryMetricRepository(max_capacity=50000)
        self.trace_repository = InMemoryTraceRepository(max_capacity=5000)
        self.span_repository = InMemorySpanRepository()
        self.audit_repository = InMemoryAuditEventRepository(max_capacity=20000)
        self.error_repository = InMemoryErrorRepository(max_capacity=5000)
        self.component_repository = InMemoryComponentRepository()
        self.execution_repository = InMemoryExecutionRepository()

        # Exporters
        self.in_memory_exporter = InMemoryExporter()
        self.exporter: TelemetryExporter
        if obs_cfg.otlp_enabled:
            self.exporter = OTLPExporter(endpoint=obs_cfg.otlp_endpoint, enabled=True)
        else:
            self.exporter = self.in_memory_exporter

        # Services
        self.redaction_service = RedactionService(
            enabled=obs_cfg.redaction_enabled,
        )

        min_log_level = LogLevel[obs_cfg.logging_level.upper()] if hasattr(LogLevel, obs_cfg.logging_level.upper()) else LogLevel.INFO
        sampling = SamplingStrategy[obs_cfg.trace_sampling.upper()] if hasattr(SamplingStrategy, obs_cfg.trace_sampling.upper()) else SamplingStrategy.ALWAYS_ON

        self.logging_service = LoggingService(
            repository=self.log_repository,
            exporter=self.exporter,
            redaction_service=self.redaction_service,
            min_level=min_log_level,
            service_name=obs_cfg.service_name,
            environment=obs_cfg.environment,
            version=obs_cfg.service_version,
        )

        self.metrics_service = MetricsService(
            repository=self.metric_repository,
            exporter=self.exporter,
            enabled=obs_cfg.metric_enabled,
        )

        self.tracing_service = TracingService(
            trace_repository=self.trace_repository,
            span_repository=self.span_repository,
            exporter=self.exporter,
            redaction_service=self.redaction_service,
            sampling_strategy=sampling,
            enabled=obs_cfg.trace_enabled,
            max_attribute_size_bytes=obs_cfg.max_attribute_size_bytes,
        )

        self.audit_service = AuditService(
            repository=self.audit_repository,
            exporter=self.exporter,
            redaction_service=self.redaction_service,
            enabled=obs_cfg.audit_enabled,
            default_retention_days=obs_cfg.retention_days,
        )

        self.error_tracking_service = ErrorTrackingService(
            repository=self.error_repository,
            metrics_service=self.metrics_service,
            redaction_service=self.redaction_service,
        )

        self.observability_service = ObservabilityService(
            log_repository=self.log_repository,
            metric_repository=self.metric_repository,
            trace_repository=self.trace_repository,
            span_repository=self.span_repository,
            audit_repository=self.audit_repository,
            error_repository=self.error_repository,
            component_repository=self.component_repository,
            execution_repository=self.execution_repository,
            logging_service=self.logging_service,
            metrics_service=self.metrics_service,
            tracing_service=self.tracing_service,
            audit_service=self.audit_service,
            error_tracking_service=self.error_tracking_service,
            redaction_service=self.redaction_service,
            enabled=obs_cfg.enabled,
        )

        self.adapter = ObservabilityAdapter(self.observability_service)

    @classmethod
    def get_instance(cls, settings: Settings | None = None) -> "ObservabilityContainer":
        """Get or initialize singleton instance of ObservabilityContainer."""
        if cls._instance is None:
            cls._instance = cls(settings)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton container (useful for test isolation)."""
        cls._instance = None
