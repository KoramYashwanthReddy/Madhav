"""API Request and Response Pydantic schemas for Module 29 REST endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from max.integrations.domain.enums import (
    AuthenticationType,
    ConnectionStatus,
)


class ConnectionCreateRequest(BaseModel):
    """Payload for creating a new external account connection."""

    provider_key: str = Field(description="Target integration provider key (e.g. mock_email, github)")
    owner_id: str = Field(default="default_user", description="Owner user ID")
    auth_data: dict[str, Any] = Field(default_factory=dict, description="Credential input data (API key, tokens, etc.)")


class ConnectionResponseSchema(BaseModel):
    """SAFE metadata view of an external account connection (NO raw credentials exposed)."""

    connection_id: str
    owner_id: str
    integration_id: str
    provider_id: str
    status: ConnectionStatus
    authentication_type: AuthenticationType
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None = None
    last_health_check_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActionExecuteRequest(BaseModel):
    """Payload for executing an external integration action."""

    owner_id: str = Field(default="default_user")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Structured arguments for action")
    timeout_seconds: float = Field(default=30.0, ge=1.0, le=300.0)
    idempotency_key: str | None = Field(default=None, description="Idempotency key to avoid duplicate side effects")
    dry_run: bool = Field(default=False, description="Dry-run flag to generate plan without side effects")


class ActionExecuteResponseSchema(BaseModel):
    """Result payload of an action execution."""

    request_id: str
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float = 0.0


class OAuthUrlRequest(BaseModel):
    """Payload for generating OAuth2 authorization URL."""

    provider_key: str
    auth_endpoint: str = Field(default="https://oauth.example.com/authorize")
    client_id: str = Field(default="max_client_123")
    redirect_uri: str = Field(default="http://localhost:8000/api/v1/integrations/oauth/callback")
    scopes: list[str] = Field(default_factory=lambda: ["read", "write"])


class OAuthUrlResponse(BaseModel):
    """OAuth2 authorization URL response."""

    authorization_url: str
    state_token: str


class OAuthCallbackRequest(BaseModel):
    """Payload for handling OAuth2 code callback exchange."""

    code: str
    state: str
    owner_id: str = Field(default="default_user")


class WebhookSubscribeRequest(BaseModel):
    """Payload for subscribing to an external webhook."""

    provider_key: str
    event_type: str = Field(default="generic.event")
    endpoint: str = Field(default="/api/v1/webhooks")
    connection_id: str | None = Field(default=None)
