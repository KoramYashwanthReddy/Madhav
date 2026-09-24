"""Comprehensive unit test suite for Module 27 — Notification System."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from max.api.router import register_routers
from max.config.sections import NotificationSettings
from max.notifications.container import get_notification_container, reset_notification_container
from max.notifications.deduplication.dedup_service import NotificationDeduplicationService
from max.notifications.domain.enums import (
    NotificationActionType,
    NotificationCategory,
    NotificationChannelType,
    NotificationReadState,
    NotificationSensitivity,
    NotificationSeverity,
    NotificationStatus,
)
from max.notifications.domain.exceptions import (
    NotificationValidationError,
)
from max.notifications.domain.models import (
    Notification,
    NotificationAction,
    NotificationContent,
    NotificationPreference,
)
from max.notifications.grouping.grouping_service import NotificationGroupingService
from max.notifications.policies.policy_service import NotificationPolicyService, PolicyDecisionEnum
from max.notifications.preferences.preference_service import NotificationPreferenceService
from max.notifications.rate_limiting.rate_limit_service import NotificationRateLimitService
from max.notifications.repositories.repositories import (
    MemoryNotificationPreferenceRepository,
    MemoryNotificationRepository,
)
from max.notifications.retry.retry_service import NotificationRetryService
from max.notifications.security.sensitivity_service import NotificationSensitivityService
from max.notifications.services.tool_integration import register_notification_tools
from max.tools.services.registry import ToolRegistryService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def notif_settings():
    return NotificationSettings()


@pytest.fixture
def repo():
    return MemoryNotificationRepository()


@pytest.fixture
def pref_repo():
    return MemoryNotificationPreferenceRepository()


@pytest.fixture
def pref_service(pref_repo):
    return NotificationPreferenceService(pref_repo)


@pytest.fixture
def policy_service(pref_service):
    return NotificationPolicyService(pref_service)


@pytest.fixture
def sensitivity_service():
    return NotificationSensitivityService()


@pytest.fixture
def test_client():
    reset_notification_container()
    app = FastAPI()
    register_routers(app)
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Domain Models & Lifecycle Tests
# ---------------------------------------------------------------------------


class TestNotificationDomainModels:
    def test_state_transitions_valid(self):
        content = NotificationContent(title="Test", body="Body")
        notif = Notification(content=content)
        assert notif.status == NotificationStatus.CREATED

        notif.transition_to(NotificationStatus.QUEUED)
        assert notif.status == NotificationStatus.QUEUED

        notif.transition_to(NotificationStatus.ROUTING)
        assert notif.status == NotificationStatus.ROUTING

        notif.transition_to(NotificationStatus.DELIVERING)
        assert notif.status == NotificationStatus.DELIVERING

        notif.transition_to(NotificationStatus.DELIVERED)
        assert notif.status == NotificationStatus.DELIVERED

    def test_invalid_state_transition_raises(self):
        content = NotificationContent(title="Test", body="Body")
        notif = Notification(content=content)
        with pytest.raises(NotificationValidationError):
            notif.transition_to(NotificationStatus.ACKNOWLEDGED)

    def test_notification_action_model(self):
        action = NotificationAction(label="View Logs", action_type=NotificationActionType.URL, target="https://logs")
        assert action.label == "View Logs"
        assert action.action_type == NotificationActionType.URL


# ---------------------------------------------------------------------------
# 2. Repository Tests
# ---------------------------------------------------------------------------


class TestNotificationRepositories:
    def test_save_and_get(self, repo):
        notif = Notification(content=NotificationContent(title="T", body="B"))
        repo.save(notif)
        fetched = repo.get(notif.notification_id)
        assert fetched.notification_id == notif.notification_id

    def test_count_unread(self, repo):
        n1 = Notification(content=NotificationContent(title="T1", body="B1"))
        n2 = Notification(content=NotificationContent(title="T2", body="B2"))
        repo.save(n1)
        repo.save(n2)
        assert repo.count_unread("user_default") == 2

        n1.read_state = NotificationReadState.READ
        repo.save(n1)
        assert repo.count_unread("user_default") == 1


# ---------------------------------------------------------------------------
# 3. Preferences & Quiet Hours Tests
# ---------------------------------------------------------------------------


class TestPreferencesAndQuietHours:
    def test_quiet_hours_span_midnight(self, pref_service):
        pref = NotificationPreference(
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
        )
        dt_night = datetime(2026, 9, 24, 23, 30, tzinfo=UTC)
        dt_day = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)

        assert pref_service.is_in_quiet_hours(pref, dt_night) is True
        assert pref_service.is_in_quiet_hours(pref, dt_day) is False

    def test_critical_severity_in_quiet_hours(self, pref_service):
        pref = NotificationPreference(
            quiet_hours_enabled=True,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
            allow_critical_in_quiet_hours=True,
        )
        dt_night = datetime(2026, 9, 24, 23, 30, tzinfo=UTC)

        permitted, reason = pref_service.is_channel_permitted(
            pref,
            channel=NotificationChannelType.IN_APP,
            severity=NotificationSeverity.CRITICAL,
            category=NotificationCategory.SECURITY,
            current_dt=dt_night,
        )
        assert permitted is True


# ---------------------------------------------------------------------------
# 4. Policy Service Tests
# ---------------------------------------------------------------------------


class TestNotificationPolicyService:
    def test_highly_sensitive_blocked_on_desktop(self, policy_service):
        notif = Notification(
            content=NotificationContent(title="Secret", body="Sensitive data"),
            sensitivity=NotificationSensitivity.HIGHLY_SENSITIVE,
        )
        res = policy_service.evaluate_channel_policy(notif, NotificationChannelType.DESKTOP)
        assert res.decision == PolicyDecisionEnum.DENY

    def test_normal_content_allowed(self, policy_service):
        notif = Notification(
            content=NotificationContent(title="Normal", body="Info"),
            sensitivity=NotificationSensitivity.INTERNAL,
        )
        res = policy_service.evaluate_channel_policy(notif, NotificationChannelType.IN_APP)
        assert res.decision == PolicyDecisionEnum.ALLOW


# ---------------------------------------------------------------------------
# 5. Deduplication, Grouping, Rate Limiting & Retry Tests
# ---------------------------------------------------------------------------


class TestDeduplicationGroupingRateLimitingRetry:
    def test_deduplication(self):
        dedup = NotificationDeduplicationService(window_seconds=10.0)
        n1 = Notification(content=NotificationContent(title="Same Title", body="Body"))
        n2 = Notification(content=NotificationContent(title="Same Title", body="Body"))

        assert dedup.is_duplicate(n1) is False
        assert dedup.is_duplicate(n2) is True

    def test_grouping(self):
        grouping = NotificationGroupingService()
        n1 = Notification(content=NotificationContent(title="T1", body="B1"))
        n2 = Notification(content=NotificationContent(title="T2", body="B2"))

        grouping.add_to_group(n1, "github_emails")
        grp2 = grouping.add_to_group(n2, "github_emails")
        assert grp2.count == 2
        assert len(grp2.member_notification_ids) == 2

    def test_rate_limiting(self):
        limiter = NotificationRateLimitService(max_per_minute=2, window_seconds=60.0)
        n = Notification(content=NotificationContent(title="T", body="B"))

        assert limiter.is_rate_limited(n, NotificationChannelType.DESKTOP) is False
        assert limiter.is_rate_limited(n, NotificationChannelType.DESKTOP) is False
        assert limiter.is_rate_limited(n, NotificationChannelType.DESKTOP) is True

    def test_retry_service(self):
        retry = NotificationRetryService(max_retries=3)
        assert retry.calculate_backoff_delay(1) == 2.0
        assert retry.calculate_backoff_delay(2) == 4.0


# ---------------------------------------------------------------------------
# 6. Sensitivity & Secret Protection Tests
# ---------------------------------------------------------------------------


class TestSensitivityAndSecretProtection:
    def test_secret_redaction(self, sensitivity_service):
        raw = "Connecting with api_key: sk-12345678901234567890123456789012"
        redacted = sensitivity_service.redact_secrets(raw)
        assert "sk-12345678901234567890123456789012" not in redacted
        assert "***REDACTED***" in redacted


# ---------------------------------------------------------------------------
# 7. NotificationService Facade Tests
# ---------------------------------------------------------------------------


class TestNotificationServiceFacade:
    @pytest.mark.asyncio
    async def test_send_notification_end_to_end(self):
        reset_notification_container()
        container = get_notification_container()

        notif = await container.service.send_notification(
            title="Task Success",
            body="Task 123 completed.",
            category=NotificationCategory.TASK,
            channels=[NotificationChannelType.IN_APP, NotificationChannelType.DESKTOP],
        )

        assert notif.status == NotificationStatus.DELIVERED
        assert len(notif.deliveries) == 2
        assert container.service.count_unread("user_default") == 1

    def test_mark_as_read_and_acknowledge(self):
        reset_notification_container()
        container = get_notification_container()

        n = Notification(content=NotificationContent(title="T", body="B"))
        n.transition_to(NotificationStatus.QUEUED)
        n.transition_to(NotificationStatus.ROUTING)
        n.transition_to(NotificationStatus.DELIVERING)
        n.transition_to(NotificationStatus.DELIVERED)
        container.repository.save(n)

        read_n = container.service.mark_as_read(n.notification_id)
        assert read_n.read_state == NotificationReadState.READ
        assert read_n.status == NotificationStatus.READ

        ack_n = container.service.acknowledge(n.notification_id, "Got it")
        assert ack_n.read_state == NotificationReadState.ACKNOWLEDGED
        assert ack_n.status == NotificationStatus.ACKNOWLEDGED


# ---------------------------------------------------------------------------
# 8. Tool Integration Tests
# ---------------------------------------------------------------------------


class TestNotificationToolIntegration:
    def test_register_notification_tools(self):
        registry = ToolRegistryService()
        ids = register_notification_tools(registry)
        assert len(ids) == 8
        tools, _ = registry.list_tools()
        names = [t.name for t in tools]
        assert "notification.send" in names
        assert "notification.get_preferences" in names


# ---------------------------------------------------------------------------
# 9. API Routes Tests
# ---------------------------------------------------------------------------


class TestNotificationAPIRoutes:
    def test_health_endpoint(self, test_client):
        resp = test_client.get("/api/v1/notifications/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_channels_endpoint(self, test_client):
        resp = test_client.get("/api/v1/notifications/channels")
        assert resp.status_code == 200
        data = resp.json()
        assert "channels" in data

    def test_templates_endpoint(self, test_client):
        resp = test_client.get("/api/v1/notifications/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["templates"]) >= 2

    def test_preferences_get_and_patch(self, test_client):
        get_resp = test_client.get("/api/v1/notifications/preferences")
        assert get_resp.status_code == 200

        patch_resp = test_client.patch(
            "/api/v1/notifications/preferences",
            json={"sound_enabled": False},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["sound_enabled"] is False

    def test_send_and_list_notifications_api(self, test_client):
        send_resp = test_client.post(
            "/api/v1/notifications",
            json={
                "title": "API Test",
                "body": "Notification from API test client",
                "category": "TASK",
            },
        )
        assert send_resp.status_code == 201
        notif = send_resp.json()
        nid = notif["notification_id"]

        list_resp = test_client.get("/api/v1/notifications")
        assert list_resp.status_code == 200
        items = list_resp.json()["notifications"]
        assert any(n["notification_id"] == nid for n in items)

        read_resp = test_client.post(f"/api/v1/notifications/{nid}/read")
        assert read_resp.status_code == 200
        assert read_resp.json()["read_state"] == "READ"
