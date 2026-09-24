"""Domain models for Module 27 — Notification System."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from max.notifications.domain.enums import (
    NotificationActionType,
    NotificationCategory,
    NotificationChannelType,
    NotificationDeliveryStatus,
    NotificationEventType,
    NotificationPriority,
    NotificationReadState,
    NotificationSensitivity,
    NotificationSeverity,
    NotificationSourceType,
    NotificationStatus,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class NotificationAction(BaseModel):
    """Interactive action intent button associated with a notification."""

    action_id: str = Field(default_factory=lambda: _generate_id("naction"))
    label: str
    action_type: NotificationActionType = Field(default=NotificationActionType.INTENT)
    target: str = Field(default="", description="URL, command name, or intent route")
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationSource(BaseModel):
    """Origin and event source identification."""

    source_type: NotificationSourceType = Field(default=NotificationSourceType.SYSTEM)
    source_id: str = Field(default="system")
    event_id: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationContent(BaseModel):
    """Payload text, title, and rich content."""

    title: str = Field(max_length=1000)
    body: str = Field(max_length=50000)
    summary: str | None = Field(default=None)
    language: str = Field(default="en")
    is_untrusted_data: bool = Field(
        default=True, description="Enforces prompt injection shielding"
    )


class NotificationRecipient(BaseModel):
    """Target user / recipient identity."""

    recipient_id: str = Field(default="user_default")
    email: str | None = Field(default=None)
    device_tokens: list[str] = Field(default_factory=list)


class NotificationDeliveryAttempt(BaseModel):
    """Log record of a single delivery attempt to a channel provider."""

    attempt_number: int = Field(ge=1)
    timestamp: datetime = Field(default_factory=_utc_now)
    status: NotificationDeliveryStatus = Field(default=NotificationDeliveryStatus.IN_PROGRESS)
    error_code: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    provider_reference: str | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)


class NotificationDelivery(BaseModel):
    """Channel-specific delivery tracking object."""

    delivery_id: str = Field(default_factory=lambda: _generate_id("ndeliv"))
    notification_id: str
    channel: NotificationChannelType
    provider_name: str = Field(default="mock")
    status: NotificationDeliveryStatus = Field(default=NotificationDeliveryStatus.QUEUED)
    attempts: list[NotificationDeliveryAttempt] = Field(default_factory=list)
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = Field(default=None)
    provider_reference: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)


class NotificationGroup(BaseModel):
    """Grouping container for aggregated notifications."""

    group_id: str = Field(default_factory=lambda: _generate_id("ngroup"))
    group_key: str
    title: str
    category: NotificationCategory = Field(default=NotificationCategory.INFO)
    member_notification_ids: list[str] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class NotificationPreference(BaseModel):
    """User preferences for channel routing, quiet hours, and category filters."""

    preference_id: str = Field(default_factory=lambda: _generate_id("npref"))
    user_id: str = Field(default="user_default")
    enabled_channels: list[NotificationChannelType] = Field(
        default_factory=lambda: [
            NotificationChannelType.IN_APP,
            NotificationChannelType.DESKTOP,
            NotificationChannelType.SPEECH,
        ]
    )
    disabled_categories: list[NotificationCategory] = Field(default_factory=list)
    min_severity_threshold: NotificationSeverity = Field(default=NotificationSeverity.LOW)
    quiet_hours_enabled: bool = Field(default=False)
    quiet_hours_start: str = Field(default="22:00", description="HH:MM format in local time")
    quiet_hours_end: str = Field(default="07:00", description="HH:MM format in local time")
    allow_critical_in_quiet_hours: bool = Field(default=True)
    sound_enabled: bool = Field(default=True)
    speech_enabled: bool = Field(default=True)
    desktop_enabled: bool = Field(default=True)
    email_enabled: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=_utc_now)


class NotificationTemplate(BaseModel):
    """Pre-defined message template for standardized notifications."""

    template_id: str = Field(default_factory=lambda: _generate_id("ntpl"))
    name: str
    category: NotificationCategory = Field(default=NotificationCategory.INFO)
    language: str = Field(default="en")
    title_template: str
    body_template: str
    variables: list[str] = Field(default_factory=list)
    version: str = Field(default="1.0.0")


class NotificationPolicy(BaseModel):
    """Policy rules dictating routing, rate limiting, and sensitivity boundaries."""

    policy_id: str = Field(default_factory=lambda: _generate_id("npol"))
    name: str
    allow_channels: list[NotificationChannelType] = Field(default_factory=list)
    max_sensitivity_allowed: NotificationSensitivity = Field(default=NotificationSensitivity.HIGHLY_SENSITIVE)
    require_acknowledgement: bool = Field(default=False)


class NotificationScheduleReference(BaseModel):
    """Clean integration reference point for Module 28 Scheduler (NO scheduler logic)."""

    schedule_reference_id: str
    scheduled_for: datetime
    trigger_rule_id: str | None = Field(default=None)


class NotificationAcknowledgement(BaseModel):
    """User acknowledgement audit model."""

    ack_id: str = Field(default_factory=lambda: _generate_id("nack"))
    notification_id: str
    user_id: str = Field(default="user_default")
    timestamp: datetime = Field(default_factory=_utc_now)
    note: str | None = Field(default=None)


class NotificationAuditEvent(BaseModel):
    """Structured observable audit event."""

    event_id: str = Field(default_factory=lambda: _generate_id("nevt"))
    notification_id: str
    event_type: NotificationEventType
    channel: NotificationChannelType | None = Field(default=None)
    status: str | None = Field(default=None)
    error_code: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=_utc_now)


class Notification(BaseModel):
    """Primary Notification Domain Entity with strict lifecycle validation."""

    notification_id: str = Field(default_factory=lambda: _generate_id("notif"))
    recipient: NotificationRecipient = Field(default_factory=NotificationRecipient)
    source: NotificationSource = Field(default_factory=NotificationSource)
    content: NotificationContent
    category: NotificationCategory = Field(default=NotificationCategory.INFO)
    severity: NotificationSeverity = Field(default=NotificationSeverity.NORMAL)
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL)
    sensitivity: NotificationSensitivity = Field(default=NotificationSensitivity.INTERNAL)
    status: NotificationStatus = Field(default=NotificationStatus.CREATED)
    read_state: NotificationReadState = Field(default=NotificationReadState.UNREAD)
    actions: list[NotificationAction] = Field(default_factory=list)
    deliveries: list[NotificationDelivery] = Field(default_factory=list)
    deduplication_key: str | None = Field(default=None)
    group_id: str | None = Field(default=None)
    schedule_reference: NotificationScheduleReference | None = Field(default=None)
    expires_at: datetime | None = Field(default=None)
    read_at: datetime | None = Field(default=None)
    acknowledged_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    def transition_to(self, target_status: NotificationStatus) -> None:
        """Validate state machine transition according to official lifecycle rules."""
        valid_transitions: dict[NotificationStatus, set[NotificationStatus]] = {
            NotificationStatus.CREATED: {
                NotificationStatus.QUEUED,
                NotificationStatus.ROUTING,
                NotificationStatus.SUPPRESSED,
                NotificationStatus.EXPIRED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.QUEUED: {
                NotificationStatus.ROUTING,
                NotificationStatus.DELIVERING,
                NotificationStatus.SUPPRESSED,
                NotificationStatus.EXPIRED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.ROUTING: {
                NotificationStatus.DELIVERING,
                NotificationStatus.DELIVERED,
                NotificationStatus.DELIVERY_FAILED,
                NotificationStatus.SUPPRESSED,
                NotificationStatus.EXPIRED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.DELIVERING: {
                NotificationStatus.DELIVERED,
                NotificationStatus.DELIVERY_FAILED,
                NotificationStatus.RETRYING,
                NotificationStatus.EXPIRED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.DELIVERED: {
                NotificationStatus.READ,
                NotificationStatus.ACKNOWLEDGED,
                NotificationStatus.EXPIRED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.READ: {
                NotificationStatus.ACKNOWLEDGED,
                NotificationStatus.EXPIRED,
            },
            NotificationStatus.ACKNOWLEDGED: set(),
            NotificationStatus.DELIVERY_FAILED: {
                NotificationStatus.RETRYING,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.RETRYING: {
                NotificationStatus.DELIVERING,
                NotificationStatus.DELIVERED,
                NotificationStatus.DELIVERY_FAILED,
                NotificationStatus.CANCELLED,
            },
            NotificationStatus.EXPIRED: set(),
            NotificationStatus.CANCELLED: set(),
            NotificationStatus.SUPPRESSED: set(),
        }

        allowed = valid_transitions.get(self.status, set())
        if target_status not in allowed and target_status != self.status:
            from max.notifications.domain.exceptions import NotificationValidationError

            raise NotificationValidationError(
                f"Invalid notification state transition from '{self.status.value}' to '{target_status.value}'.",
                details={"current_status": self.status.value, "target_status": target_status.value},
            )

        self.status = target_status
        self.updated_at = _utc_now()
