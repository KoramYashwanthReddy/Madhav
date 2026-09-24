"""Domain entities for Module 29 — External Integrations."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from max.integrations.domain.enums import (
    AuthenticationType,
    ConnectionStatus,
    ErrorCode,
    IntegrationCategory,
    IntegrationStatus,
    RiskLevel,
    WebhookProcessingStatus,
)


class CredentialReference(BaseModel):
    """Reference identifier for credentials stored in SecretStore.

    CRITICAL: Never store or log raw secrets (tokens, API keys, client secrets).
    """

    credential_id: str = Field(
        default_factory=lambda: f"cred_{uuid4().hex[:12]}",
        description="Opaque pointer to secret in SecretStore",
    )
    credential_type: AuthenticationType = Field(description="Auth type of referenced credentials")
    provider_key: str = Field(description="Associated integration provider key")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Safe metadata (e.g. scopes, issuer)")


class IntegrationCapability(BaseModel):
    """Capability descriptor exposed by an integration provider."""

    capability_id: str = Field(default_factory=lambda: f"cap_{uuid4().hex[:8]}")
    name: str = Field(description="Capability display name (e.g. calendar.create_event)")
    description: str = Field(default="")
    category: IntegrationCategory = Field(default=IntegrationCategory.OTHER)
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM)
    input_schema: dict[str, Any] = Field(default_factory=dict, description="JSON schema for parameters")
    output_schema: dict[str, Any] = Field(default_factory=dict, description="JSON schema for result")
    required_permissions: list[str] = Field(default_factory=list, description="Module 15 permission requirements")


class IntegrationAction(BaseModel):
    """Structured action definition mapping to an integration capability."""

    action_id: str = Field(default_factory=lambda: f"act_{uuid4().hex[:8]}")
    integration_id: str = Field(description="Target integration ID")
    capability_id: str = Field(description="Associated capability ID")
    name: str = Field(description="Action name (e.g. send_email)")
    description: str = Field(default="")
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM)


class Integration(BaseModel):
    """Integration entity representing an external service integration definition."""

    integration_id: str = Field(default_factory=lambda: f"intg_{uuid4().hex[:12]}")
    integration_key: str = Field(description="Unique string key (e.g. github, google_calendar)")
    name: str = Field(description="Integration display name")
    description: str = Field(default="")
    category: IntegrationCategory = Field(default=IntegrationCategory.OTHER)
    version: str = Field(default="1.0.0")
    status: IntegrationStatus = Field(default=IntegrationStatus.ACTIVE)
    capabilities: list[IntegrationCapability] = Field(default_factory=list)
    actions: list[IntegrationAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationProvider(BaseModel):
    """Provider registration metadata."""

    provider_id: str = Field(default_factory=lambda: f"prov_{uuid4().hex[:12]}")
    provider_key: str = Field(description="Unique provider key matching integration")
    name: str = Field(description="Provider display name")
    version: str = Field(default="1.0.0")
    base_configuration: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[IntegrationCapability] = Field(default_factory=list)
    status: IntegrationStatus = Field(default=IntegrationStatus.ACTIVE)


class IntegrationConnection(BaseModel):
    """Authenticated account connection instance to an external provider."""

    connection_id: str = Field(default_factory=lambda: f"conn_{uuid4().hex[:12]}")
    owner_id: str = Field(default="default_user", description="Owner user ID")
    integration_id: str = Field(description="Referenced integration ID")
    provider_id: str = Field(description="Referenced provider ID")
    status: ConnectionStatus = Field(default=ConnectionStatus.PENDING)
    authentication_type: AuthenticationType = Field(default=AuthenticationType.API_KEY)
    credential_ref: CredentialReference | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = Field(default=None)
    last_health_check_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationRequest(BaseModel):
    """Structured request payload for invoking an external action."""

    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    connection_id: str = Field(description="Target connection ID")
    action_id: str = Field(description="Target action ID or capability name")
    owner_id: str = Field(default="default_user")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Action arguments")
    timeout_seconds: float = Field(default=30.0)
    idempotency_key: str | None = Field(default=None, description="Idempotency key to avoid duplicate side effects")
    dry_run: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationResponse(BaseModel):
    """Structured result returned by an external action invocation."""

    request_id: str = Field(description="Correlated request ID")
    status: str = Field(default="SUCCESS", description="SUCCESS, FAILED, or DRY_RUN")
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provider_request_id: str | None = Field(default=None)
    latency_ms: float = Field(default=0.0)


class IntegrationErrorModel(BaseModel):
    """Structured normalized provider error data."""

    error_code: ErrorCode = Field(default=ErrorCode.UNKNOWN)
    category: str = Field(default="GENERAL")
    message: str = Field(description="Normalized human-readable error message")
    retryable: bool = Field(default=False)
    provider_code: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookSubscription(BaseModel):
    """Webhook subscription registration entity."""

    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid4().hex[:12]}")
    integration_id: str = Field(description="Referenced integration ID")
    connection_id: str | None = Field(default=None)
    event_type: str = Field(description="Event type name (e.g. github.push)")
    endpoint: str = Field(description="Registered webhook endpoint URI")
    secret_reference: CredentialReference | None = Field(default=None)
    status: str = Field(default="ACTIVE")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WebhookEvent(BaseModel):
    """Ingested webhook event record."""

    event_id: str = Field(default_factory=lambda: f"whev_{uuid4().hex[:12]}")
    integration_id: str = Field(description="Target integration ID")
    provider_id: str = Field(description="Source provider ID")
    event_type: str = Field(description="Event type string")
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload_reference: str = Field(description="Reference or hash of raw payload")
    signature_status: str = Field(default="VALID", description="VALID, INVALID, or UNVERIFIED")
    processing_status: WebhookProcessingStatus = Field(default=WebhookProcessingStatus.RECEIVED)


class ExternalEvent(BaseModel):
    """Provider-neutral normalized external event object."""

    event_id: str = Field(default_factory=lambda: f"extev_{uuid4().hex[:12]}")
    source: str = Field(description="Source provider name")
    integration_id: str = Field(description="Associated integration ID")
    event_type: str = Field(description="Normalized event name (e.g. github.pull_request.created)")
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = Field(default_factory=dict, description="Sanitized untrusted event data")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationAuditEvent(BaseModel):
    """Auditable log record for integration operations."""

    event_id: str = Field(default_factory=lambda: f"audit_{uuid4().hex[:12]}")
    owner_id: str = Field(default="system")
    integration_id: str = Field(description="Target integration ID")
    connection_id: str | None = Field(default=None)
    action: str = Field(description="Action name (e.g. CONNECT, EXECUTE, WEBHOOK)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    result: str = Field(default="SUCCESS")
    metadata: dict[str, Any] = Field(default_factory=dict)
