"""FastAPI REST API routes for Module 29 — External Integrations."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status

from max.integrations.container import get_integration_container
from max.integrations.domain.exceptions import (
    ActionExecutionError,
    ConnectionNotFoundError,
    IntegrationError,
    InvalidWebhookSignatureError,
    PermissionDeniedIntegrationError,
    ProviderNotFoundError,
    RateLimitExceededError,
)
from max.integrations.domain.models import IntegrationRequest
from max.integrations.schemas.integration_schemas import (
    ActionExecuteRequest,
    ActionExecuteResponseSchema,
    ConnectionCreateRequest,
    ConnectionResponseSchema,
    OAuthCallbackRequest,
    OAuthUrlRequest,
    OAuthUrlResponse,
    WebhookSubscribeRequest,
)

integrations_router = APIRouter(prefix="/integrations", tags=["External Integrations Engine"])
connections_router = APIRouter(prefix="/connections", tags=["Integration Connections"])
webhooks_router = APIRouter(prefix="/webhooks", tags=["Webhook Ingestion Framework"])


# =========================================================
# Integrations Metadata & Discovery
# =========================================================

@integrations_router.get("", status_code=status.HTTP_200_OK)
def list_integrations(category: str | None = Query(default=None)) -> list[dict[str, Any]]:
    """List registered external integrations."""
    container = get_integration_container()
    intgs = container.registry.list_integrations(category=category)
    return [i.model_dump() for i in intgs]


@integrations_router.get("/{integration_id}", status_code=status.HTTP_200_OK)
def get_integration(integration_id: str) -> dict[str, Any]:
    """Get single integration definition."""
    container = get_integration_container()
    try:
        intg, _ = container.registry.resolve_action(integration_id, "list")
        return intg.model_dump()
    except Exception:
        intgs = container.registry.list_integrations()
        for i in intgs:
            if i.integration_id == integration_id or i.integration_key == integration_id:
                return i.model_dump()
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found.") from None


@integrations_router.get("/{integration_id}/capabilities", status_code=status.HTTP_200_OK)
def get_capabilities(integration_id: str) -> list[dict[str, Any]]:
    """List capabilities for an integration."""
    container = get_integration_container()
    prov_key = integration_id.replace("intg_", "")
    try:
        caps = container.registry.discover_capabilities(prov_key)
        return [c.model_dump() for c in caps]
    except ProviderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@integrations_router.post("/oauth/url", status_code=status.HTTP_200_OK, response_model=OAuthUrlResponse)
def get_oauth_url(payload: OAuthUrlRequest) -> OAuthUrlResponse:
    """Generate OAuth2 authorization URL with secure CSRF state token."""
    container = get_integration_container()
    url, state = container.oauth2_handler.generate_authorization_url(
        provider_key=payload.provider_key,
        auth_endpoint=payload.auth_endpoint,
        client_id=payload.client_id,
        redirect_uri=payload.redirect_uri,
        scopes=payload.scopes,
    )
    return OAuthUrlResponse(authorization_url=url, state_token=state)


@integrations_router.post("/oauth/callback", status_code=status.HTTP_200_OK, response_model=ConnectionResponseSchema)
def handle_oauth_callback(payload: OAuthCallbackRequest) -> ConnectionResponseSchema:
    """Handle OAuth2 callback authorization code exchange."""
    container = get_integration_container()
    try:
        cred_ref = container.oauth2_handler.exchange_code_mock(
            code=payload.code,
            state_token=payload.state,
            secret_store=container.secret_store,
            owner_id=payload.owner_id,
        )
        conn = container.connection_service.connect_account(
            provider_key=cred_ref.provider_key,
            owner_id=payload.owner_id,
            auth_data={"oauth": True, "scopes": cred_ref.metadata.get("scopes")},
        )
        return ConnectionResponseSchema(**conn.model_dump())
    except IntegrationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


# =========================================================
# Connections Lifecycle & Execution
# =========================================================

@connections_router.post("", status_code=status.HTTP_201_CREATED, response_model=ConnectionResponseSchema)
def create_connection(payload: ConnectionCreateRequest) -> ConnectionResponseSchema:
    """Establish a new external account connection."""
    container = get_integration_container()
    try:
        conn = container.connection_service.connect_account(
            provider_key=payload.provider_key,
            owner_id=payload.owner_id,
            auth_data=payload.auth_data,
        )
        return ConnectionResponseSchema(**conn.model_dump())
    except IntegrationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@connections_router.get("", status_code=status.HTTP_200_OK, response_model=list[ConnectionResponseSchema])
def list_connections(
    owner_id: str = Query(default="default_user"),
    integration_id: str | None = Query(default=None),
) -> list[ConnectionResponseSchema]:
    """List connections for an owner."""
    container = get_integration_container()
    conns = container.connection_service.list_connections(owner_id=owner_id, integration_id=integration_id)
    return [ConnectionResponseSchema(**c.model_dump()) for c in conns]


@connections_router.get("/{connection_id}", status_code=status.HTTP_200_OK, response_model=ConnectionResponseSchema)
def get_connection(connection_id: str) -> ConnectionResponseSchema:
    """Get connection metadata."""
    container = get_integration_container()
    try:
        conn = container.connection_service.get_connection(connection_id)
        return ConnectionResponseSchema(**conn.model_dump())
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@connections_router.post("/{connection_id}/health", status_code=status.HTTP_200_OK)
def check_connection_health(connection_id: str) -> dict[str, Any]:
    """Perform health check on a connection."""
    container = get_integration_container()
    try:
        return container.connection_service.health_check(connection_id)
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@connections_router.post("/{connection_id}/disconnect", status_code=status.HTTP_200_OK)
def disconnect_connection(connection_id: str) -> dict[str, Any]:
    """Disconnect account connection."""
    container = get_integration_container()
    try:
        ok = container.connection_service.disconnect_account(connection_id)
        return {"connection_id": connection_id, "disconnected": ok}
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@connections_router.post("/{connection_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_connection(connection_id: str) -> dict[str, Any]:
    """Revoke account connection immediately."""
    container = get_integration_container()
    try:
        ok = container.connection_service.revoke_connection(connection_id)
        return {"connection_id": connection_id, "revoked": ok}
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@connections_router.post(
    "/{connection_id}/actions/{action_id}",
    status_code=status.HTTP_200_OK,
    response_model=ActionExecuteResponseSchema,
)
def execute_action(
    connection_id: str, action_id: str, payload: ActionExecuteRequest
) -> ActionExecuteResponseSchema:
    """Execute an external integration action."""
    container = get_integration_container()
    req = IntegrationRequest(
        connection_id=connection_id,
        action_id=action_id,
        owner_id=payload.owner_id,
        arguments=payload.arguments,
        timeout_seconds=payload.timeout_seconds,
        idempotency_key=payload.idempotency_key,
        dry_run=payload.dry_run,
    )
    try:
        res = container.execution_service.execute_action(req)
        return ActionExecuteResponseSchema(**res.model_dump())
    except ConnectionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionDeniedIntegrationError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except RateLimitExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except ActionExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# =========================================================
# Webhook Ingestion & Subscriptions
# =========================================================

@webhooks_router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_webhook(payload: WebhookSubscribeRequest) -> dict[str, Any]:
    """Subscribe to external webhook events."""
    container = get_integration_container()
    try:
        sub = container.webhook_service.subscribe_webhook(
            provider_key=payload.provider_key,
            event_type=payload.event_type,
            endpoint=payload.endpoint,
            connection_id=payload.connection_id,
        )
        return sub.model_dump()
    except IntegrationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc


@webhooks_router.post("/{subscription_id}/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe_webhook(subscription_id: str) -> dict[str, Any]:
    """Unsubscribe from external webhook events."""
    container = get_integration_container()
    ok = container.webhook_service.unsubscribe_webhook(subscription_id)
    return {"subscription_id": subscription_id, "unsubscribed": ok}


@webhooks_router.post("/{integration_id}", status_code=status.HTTP_200_OK)
async def ingest_webhook(integration_id: str, request: Request) -> dict[str, Any]:
    """Ingest, validate, normalize, and forward incoming external webhooks."""
    container = get_integration_container()
    headers = dict(request.headers)
    body_bytes = await request.body()
    payload_str = body_bytes.decode("utf-8")

    try:
        payload_obj = await request.json()
    except Exception:
        payload_obj = payload_str

    try:
        ext_event = container.webhook_service.ingest_webhook(
            integration_id_or_key=integration_id,
            headers=headers,
            payload=payload_obj,
        )
        return {"status": "ACCEPTED", "event_id": ext_event.event_id, "event_type": ext_event.event_type}
    except InvalidWebhookSignatureError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except IntegrationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
