"""FastAPI router for Module 27 — Notification System."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from max.notifications.container import get_notification_container
from max.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannelType,
    NotificationPriority,
    NotificationReadState,
    NotificationSensitivity,
    NotificationSeverity,
    NotificationSourceType,
)
from max.notifications.domain.exceptions import (
    NotificationChannelError,
    NotificationError,
    NotificationNotFoundError,
    NotificationPermissionError,
    NotificationPolicyError,
    NotificationRateLimitError,
    NotificationValidationError,
)

router = APIRouter(prefix="/notifications", tags=["Notification System"])


# ---------------------------------------------------------------------------
# API Request / Response Schemas
# ---------------------------------------------------------------------------


class CreateNotificationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    body: str = Field(min_length=1, max_length=50000)
    recipient_id: str = "user_default"
    category: NotificationCategory = NotificationCategory.INFO
    severity: NotificationSeverity = NotificationSeverity.NORMAL
    priority: NotificationPriority = NotificationPriority.NORMAL
    sensitivity: NotificationSensitivity = NotificationSensitivity.INTERNAL
    source_type: NotificationSourceType = NotificationSourceType.SYSTEM
    source_id: str = "system"
    channels: list[NotificationChannelType] | None = None
    deduplication_key: str | None = None
    group_key: str | None = None


class AcknowledgeRequest(BaseModel):
    note: str | None = None


class UpdatePreferencesRequest(BaseModel):
    enabled_channels: list[NotificationChannelType] | None = None
    disabled_categories: list[NotificationCategory] | None = None
    min_severity_threshold: NotificationSeverity | None = None
    quiet_hours_enabled: bool | None = None
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    allow_critical_in_quiet_hours: bool | None = None
    sound_enabled: bool | None = None
    speech_enabled: bool | None = None
    desktop_enabled: bool | None = None
    email_enabled: bool | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_notification_error(exc: Exception) -> None:
    """Map notification exceptions to FastAPI HTTP responses."""
    if isinstance(exc, NotificationPermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, NotificationNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, NotificationValidationError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, (NotificationRateLimitError, NotificationPolicyError)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))
    if isinstance(exc, NotificationChannelError):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    if isinstance(exc, NotificationError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """Return Notification System subsystem health status."""
    container = get_notification_container()
    return {
        "status": "healthy",
        "subsystem": "notification_system",
        "enabled": container.settings.enabled,
        "default_channel": container.settings.default_channel,
        "channels": [c.value for c in container.channel_registry.list_channels()],
    }


@router.get("/unread/count", status_code=status.HTTP_200_OK)
async def count_unread(recipient_id: str = Query(default="user_default")) -> dict[str, Any]:
    """Return count of unread notifications for recipient."""
    try:
        container = get_notification_container()
        count = container.service.count_unread(recipient_id)
        return {"recipient_id": recipient_id, "unread_count": count}
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.get("/preferences", status_code=status.HTTP_200_OK)
async def get_preferences(user_id: str = Query(default="user_default")) -> dict[str, Any]:
    """Get user notification preferences."""
    try:
        container = get_notification_container()
        pref = container.service.get_preferences(user_id)
        return pref.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.patch("/preferences", status_code=status.HTTP_200_OK)
async def update_preferences(
    request: UpdatePreferencesRequest, user_id: str = Query(default="user_default")
) -> dict[str, Any]:
    """Update user notification preferences."""
    try:
        container = get_notification_container()
        updates = {k: v for k, v in request.model_dump().items() if v is not None}
        pref = container.service.update_preferences(user_id, **updates)
        return pref.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.get("/channels", status_code=status.HTTP_200_OK)
async def list_channels() -> dict[str, Any]:
    """List available notification delivery channels."""
    container = get_notification_container()
    channels = container.channel_registry.list_channels()
    return {"channels": [c.value for c in channels]}


@router.get("/templates", status_code=status.HTTP_200_OK)
async def list_templates() -> dict[str, Any]:
    """List available message templates."""
    container = get_notification_container()
    templates = container.template_repository.list_templates()
    return {"templates": [t.model_dump() for t in templates]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_notification(request: CreateNotificationRequest) -> dict[str, Any]:
    """Create, route, and deliver a notification."""
    try:
        container = get_notification_container()
        notification = await container.service.send_notification(
            title=request.title,
            body=request.body,
            recipient_id=request.recipient_id,
            category=request.category,
            severity=request.severity,
            priority=request.priority,
            sensitivity=request.sensitivity,
            source_type=request.source_type,
            source_id=request.source_id,
            channels=request.channels,
            deduplication_key=request.deduplication_key,
            group_key=request.group_key,
        )
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.get("", status_code=status.HTTP_200_OK)
async def list_notifications(
    recipient_id: str = Query(default="user_default"),
    category: NotificationCategory | None = Query(default=None),
    severity: NotificationSeverity | None = Query(default=None),
    read_state: NotificationReadState | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List notification history with filters and pagination."""
    try:
        container = get_notification_container()
        items = container.service.list_notifications(
            recipient_id=recipient_id,
            category=category,
            severity=severity,
            read_state=read_state,
            limit=limit,
            offset=offset,
        )
        return {
            "notifications": [n.model_dump() for n in items],
            "limit": limit,
            "offset": offset,
            "count": len(items),
        }
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.get("/{notification_id}", status_code=status.HTTP_200_OK)
async def get_notification(notification_id: str) -> dict[str, Any]:
    """Retrieve details for a specific notification."""
    try:
        container = get_notification_container()
        notification = container.repository.get(notification_id)
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.post("/{notification_id}/read", status_code=status.HTTP_200_OK)
async def mark_read(notification_id: str) -> dict[str, Any]:
    """Mark a notification as READ."""
    try:
        container = get_notification_container()
        notification = container.service.mark_as_read(notification_id)
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.post("/{notification_id}/acknowledge", status_code=status.HTTP_200_OK)
async def acknowledge(notification_id: str, request: AcknowledgeRequest | None = None) -> dict[str, Any]:
    """Mark a notification as ACKNOWLEDGED."""
    try:
        container = get_notification_container()
        note = request.note if request else None
        notification = container.service.acknowledge(notification_id, note)
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.post("/{notification_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss(notification_id: str) -> dict[str, Any]:
    """Dismiss a notification."""
    try:
        container = get_notification_container()
        notification = container.service.dismiss(notification_id)
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.post("/{notification_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel(notification_id: str) -> dict[str, Any]:
    """Cancel a notification."""
    try:
        container = get_notification_container()
        notification = await container.service.cancel_notification(notification_id)
        return notification.model_dump()
    except Exception as exc:
        _handle_notification_error(exc)
        return {}


@router.get("/{notification_id}/deliveries", status_code=status.HTTP_200_OK)
async def list_deliveries(notification_id: str) -> dict[str, Any]:
    """List delivery attempt history for a specific notification."""
    try:
        container = get_notification_container()
        deliveries = container.delivery_repository.list_by_notification(notification_id)
        return {"deliveries": [d.model_dump() for d in deliveries]}
    except Exception as exc:
        _handle_notification_error(exc)
        return {}
