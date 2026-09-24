"""Deterministic Mock Integration Providers for Module 29 testing and offline development."""

import hashlib
import hmac
import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from max.integrations.domain.enums import (
    AuthenticationType,
    ConnectionStatus,
    ErrorCode,
    IntegrationCategory,
    RiskLevel,
)
from max.integrations.domain.exceptions import ActionExecutionError, InvalidWebhookSignatureError
from max.integrations.domain.models import (
    CredentialReference,
    ExternalEvent,
    IntegrationCapability,
    IntegrationConnection,
    IntegrationResponse,
    WebhookSubscription,
)
from max.integrations.providers.base_provider import ExternalIntegrationProvider
from max.integrations.secrets.secret_store import SecretStore

logger = logging.getLogger(__name__)


# =========================================================
# Base Helper for Mock Providers
# =========================================================

class BaseMockProvider(ExternalIntegrationProvider):
    """Base mock implementation managing credential references cleanly."""

    def _create_connection_and_cred(
        self,
        owner_id: str,
        auth_data: dict[str, Any],
        secret_store: SecretStore,
        auth_type: AuthenticationType,
    ) -> tuple[IntegrationConnection, CredentialReference]:
        conn_id = f"conn_{uuid4().hex[:12]}"
        cred_id = f"cred_{uuid4().hex[:12]}"

        # Store raw secret dictionary in SecretStore
        secret_store.store(cred_id, auth_data)

        cred_ref = CredentialReference(
            credential_id=cred_id,
            credential_type=auth_type,
            provider_key=self.provider_key,
            metadata={"scopes": auth_data.get("scopes", ["read", "write"])},
        )

        conn = IntegrationConnection(
            connection_id=conn_id,
            owner_id=owner_id,
            integration_id=f"intg_{self.provider_key}",
            provider_id=f"prov_{self.provider_key}",
            status=ConnectionStatus.ACTIVE,
            authentication_type=auth_type,
            credential_ref=cred_ref,
        )
        return conn, cred_ref

    def disconnect(self, connection: IntegrationConnection, secret_store: SecretStore) -> bool:
        if connection.credential_ref:
            secret_store.delete(connection.credential_ref.credential_id)
        connection.status = ConnectionStatus.DISCONNECTED
        return True

    def authenticate(self, connection: IntegrationConnection, secret_store: SecretStore) -> bool:
        if not connection.credential_ref:
            return False
        return secret_store.exists(connection.credential_ref.credential_id)

    def refresh_credentials(
        self, connection: IntegrationConnection, secret_store: SecretStore
    ) -> IntegrationConnection:
        if connection.credential_ref and secret_store.exists(connection.credential_ref.credential_id):
            secrets = secret_store.retrieve(connection.credential_ref.credential_id)
            secrets["refreshed_at"] = datetime.now(UTC).isoformat()
            secret_store.rotate(connection.credential_ref.credential_id, secrets)
            connection.status = ConnectionStatus.ACTIVE
            connection.updated_at = datetime.now(UTC)
        return connection

    def health_check(self, connection: IntegrationConnection, secret_store: SecretStore) -> dict[str, Any]:
        is_auth = self.authenticate(connection, secret_store)
        connection.last_health_check_at = datetime.now(UTC)
        if not is_auth:
            connection.status = ConnectionStatus.ERROR
            return {"status": "ERROR", "healthy": False, "latency_ms": 1.2, "reason": "Credentials missing"}
        return {"status": "HEALTHY", "healthy": True, "latency_ms": 2.5}


# =========================================================
# 1. Mock Email Provider
# =========================================================

class MockEmailProvider(BaseMockProvider):
    @property
    def provider_key(self) -> str:
        return "mock_email"

    @property
    def name(self) -> str:
        return "Mock Email Service"

    @property
    def category(self) -> IntegrationCategory:
        return IntegrationCategory.EMAIL

    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        return self._create_connection_and_cred(owner_id, auth_data, secret_store, AuthenticationType.API_KEY)

    def list_capabilities(self) -> list[IntegrationCapability]:
        return [
            IntegrationCapability(
                capability_id="email.send",
                name="email.send",
                description="Send an email to specified recipients",
                category=IntegrationCategory.EMAIL,
                risk_level=RiskLevel.HIGH,
                input_schema={"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"message_id": {"type": "string"}, "status": {"type": "string"}}},
            ),
            IntegrationCapability(
                capability_id="email.read",
                name="email.read",
                description="Read email by message ID",
                category=IntegrationCategory.EMAIL,
                risk_level=RiskLevel.MEDIUM,
                input_schema={"type": "object", "properties": {"message_id": {"type": "string"}}},
                output_schema={"type": "object"},
            ),
            IntegrationCapability(
                capability_id="email.search",
                name="email.search",
                description="Search inbox emails matching query",
                category=IntegrationCategory.EMAIL,
                risk_level=RiskLevel.LOW,
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "array"},
            ),
        ]

    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        req_id = f"req_{uuid4().hex[:12]}"
        if action_id == "email.send":
            to = args.get("to", "user@example.com")
            subj = args.get("subject", "No subject")
            msg_id = f"msg_{uuid4().hex[:8]}"
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"message_id": msg_id, "to": to, "subject": subj, "delivered": True},
                latency_ms=15.0,
            )
        elif action_id == "email.read":
            msg_id = args.get("message_id", "msg_123")
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"message_id": msg_id, "subject": "Mock Subject", "from": "sender@example.com", "body": "Mock email body content."},
                latency_ms=10.0,
            )
        elif action_id == "email.search":
            q = args.get("query", "")
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"results": [{"message_id": "msg_001", "subject": f"SearchResult for {q}"}], "total": 1},
                latency_ms=12.0,
            )
        raise ActionExecutionError(action_id, ErrorCode.NOT_FOUND.value, f"Unknown action '{action_id}'")

    def subscribe_webhook(
        self, connection: IntegrationConnection | None, event_type: str, endpoint: str, secret_store: SecretStore
    ) -> WebhookSubscription:
        sec_id = f"whsec_{uuid4().hex[:8]}"
        secret_store.store(sec_id, {"secret": "mock_email_webhook_secret_key"})
        cred_ref = CredentialReference(credential_id=sec_id, credential_type=AuthenticationType.API_KEY, provider_key=self.provider_key)
        return WebhookSubscription(
            integration_id="intg_mock_email",
            connection_id=connection.connection_id if connection else None,
            event_type=event_type,
            endpoint=endpoint,
            secret_reference=cred_ref,
        )

    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        if subscription.secret_reference:
            secret_store.delete(subscription.secret_reference.credential_id)
        return True

    def handle_webhook(
        self,
        headers: dict[str, str],
        payload: dict[str, Any] | str,
        subscription: WebhookSubscription,
        secret_store: SecretStore,
    ) -> ExternalEvent:
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        return ExternalEvent(
            source=self.provider_key,
            integration_id=subscription.integration_id,
            event_type=f"email.{data.get('event', 'received')}",
            payload=data,
        )


# =========================================================
# 2. Mock Calendar Provider
# =========================================================

class MockCalendarProvider(BaseMockProvider):
    @property
    def provider_key(self) -> str:
        return "mock_calendar"

    @property
    def name(self) -> str:
        return "Mock Calendar Service"

    @property
    def category(self) -> IntegrationCategory:
        return IntegrationCategory.CALENDAR

    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        return self._create_connection_and_cred(owner_id, auth_data, secret_store, AuthenticationType.OAUTH2)

    def list_capabilities(self) -> list[IntegrationCapability]:
        return [
            IntegrationCapability(
                capability_id="calendar.list_events",
                name="calendar.list_events",
                description="List events within a time range",
                category=IntegrationCategory.CALENDAR,
                risk_level=RiskLevel.LOW,
            ),
            IntegrationCapability(
                capability_id="calendar.create_event",
                name="calendar.create_event",
                description="Create a new calendar event",
                category=IntegrationCategory.CALENDAR,
                risk_level=RiskLevel.HIGH,
            ),
            IntegrationCapability(
                capability_id="calendar.update_event",
                name="calendar.update_event",
                description="Update an existing calendar event",
                category=IntegrationCategory.CALENDAR,
                risk_level=RiskLevel.HIGH,
            ),
            IntegrationCapability(
                capability_id="calendar.delete_event",
                name="calendar.delete_event",
                description="Delete a calendar event",
                category=IntegrationCategory.CALENDAR,
                risk_level=RiskLevel.CRITICAL,
            ),
        ]

    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        req_id = f"req_{uuid4().hex[:12]}"
        if action_id == "calendar.list_events":
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"events": [{"event_id": "evt_001", "title": "Team Sync", "start": "2026-09-25T10:00:00Z"}]},
            )
        elif action_id == "calendar.create_event":
            evt_id = f"evt_{uuid4().hex[:8]}"
            title = args.get("title", "New Event")
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"event_id": evt_id, "title": title, "created": True},
            )
        elif action_id == "calendar.update_event":
            evt_id = args.get("event_id", "evt_001")
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"event_id": evt_id, "updated": True},
            )
        elif action_id == "calendar.delete_event":
            evt_id = args.get("event_id", "evt_001")
            return IntegrationResponse(
                request_id=req_id,
                status="SUCCESS",
                data={"event_id": evt_id, "deleted": True},
            )
        raise ActionExecutionError(action_id, ErrorCode.NOT_FOUND.value, f"Unknown action '{action_id}'")

    def subscribe_webhook(
        self, connection: IntegrationConnection | None, event_type: str, endpoint: str, secret_store: SecretStore
    ) -> WebhookSubscription:
        sec_id = f"whsec_{uuid4().hex[:8]}"
        secret_store.store(sec_id, {"secret": "cal_secret"})
        return WebhookSubscription(
            integration_id="intg_mock_calendar",
            connection_id=connection.connection_id if connection else None,
            event_type=event_type,
            endpoint=endpoint,
            secret_reference=CredentialReference(credential_id=sec_id, credential_type=AuthenticationType.API_KEY, provider_key=self.provider_key),
        )

    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        return True

    def handle_webhook(
        self, headers: dict[str, str], payload: dict[str, Any] | str, subscription: WebhookSubscription, secret_store: SecretStore
    ) -> ExternalEvent:
        data = json.loads(payload) if isinstance(payload, str) else payload
        return ExternalEvent(
            source=self.provider_key,
            integration_id=subscription.integration_id,
            event_type=f"calendar.{data.get('event', 'updated')}",
            payload=data,
        )


# =========================================================
# 3. Mock Storage Provider
# =========================================================

class MockStorageProvider(BaseMockProvider):
    @property
    def provider_key(self) -> str:
        return "mock_storage"

    @property
    def name(self) -> str:
        return "Mock Cloud Storage Service"

    @property
    def category(self) -> IntegrationCategory:
        return IntegrationCategory.STORAGE

    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        return self._create_connection_and_cred(owner_id, auth_data, secret_store, AuthenticationType.BEARER_TOKEN)

    def list_capabilities(self) -> list[IntegrationCapability]:
        return [
            IntegrationCapability(capability_id="storage.list", name="storage.list", category=IntegrationCategory.STORAGE, risk_level=RiskLevel.LOW),
            IntegrationCapability(capability_id="storage.read", name="storage.read", category=IntegrationCategory.STORAGE, risk_level=RiskLevel.MEDIUM),
            IntegrationCapability(capability_id="storage.upload", name="storage.upload", category=IntegrationCategory.STORAGE, risk_level=RiskLevel.HIGH),
            IntegrationCapability(capability_id="storage.delete", name="storage.delete", category=IntegrationCategory.STORAGE, risk_level=RiskLevel.CRITICAL),
        ]

    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        req_id = f"req_{uuid4().hex[:12]}"
        if action_id == "storage.list":
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"files": [{"path": "/docs/file1.txt", "size": 1024}]})
        elif action_id == "storage.read":
            path = args.get("path", "/docs/file1.txt")
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"path": path, "content": "Mock file content"})
        elif action_id == "storage.upload":
            path = args.get("path", "/docs/new.txt")
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"path": path, "uploaded": True})
        elif action_id == "storage.delete":
            path = args.get("path", "/docs/old.txt")
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"path": path, "deleted": True})
        raise ActionExecutionError(action_id, ErrorCode.NOT_FOUND.value, f"Unknown action '{action_id}'")

    def subscribe_webhook(
        self, connection: IntegrationConnection | None, event_type: str, endpoint: str, secret_store: SecretStore
    ) -> WebhookSubscription:
        sec_id = f"whsec_{uuid4().hex[:8]}"
        secret_store.store(sec_id, {"secret": "storage_secret"})
        return WebhookSubscription(
            integration_id="intg_mock_storage",
            connection_id=connection.connection_id if connection else None,
            event_type=event_type,
            endpoint=endpoint,
            secret_reference=CredentialReference(credential_id=sec_id, credential_type=AuthenticationType.API_KEY, provider_key=self.provider_key),
        )

    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        return True

    def handle_webhook(
        self, headers: dict[str, str], payload: dict[str, Any] | str, subscription: WebhookSubscription, secret_store: SecretStore
    ) -> ExternalEvent:
        data = json.loads(payload) if isinstance(payload, str) else payload
        return ExternalEvent(source=self.provider_key, integration_id=subscription.integration_id, event_type="storage.object_changed", payload=data)


# =========================================================
# 4. Mock GitHub Provider
# =========================================================

class MockGitHubProvider(BaseMockProvider):
    @property
    def provider_key(self) -> str:
        return "mock_github"

    @property
    def name(self) -> str:
        return "Mock GitHub Service"

    @property
    def category(self) -> IntegrationCategory:
        return IntegrationCategory.DEVELOPER

    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        return self._create_connection_and_cred(owner_id, auth_data, secret_store, AuthenticationType.BEARER_TOKEN)

    def list_capabilities(self) -> list[IntegrationCapability]:
        return [
            IntegrationCapability(capability_id="repository.read", name="repository.read", category=IntegrationCategory.DEVELOPER, risk_level=RiskLevel.LOW),
            IntegrationCapability(capability_id="issue.create", name="issue.create", category=IntegrationCategory.DEVELOPER, risk_level=RiskLevel.HIGH),
            IntegrationCapability(capability_id="pull_request.read", name="pull_request.read", category=IntegrationCategory.DEVELOPER, risk_level=RiskLevel.LOW),
        ]

    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        req_id = f"req_{uuid4().hex[:12]}"
        if action_id == "repository.read":
            repo = args.get("repository", "owner/repo")
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"repository": repo, "stars": 42, "forks": 10})
        elif action_id == "issue.create":
            title = args.get("title", "New Issue")
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"issue_id": 101, "title": title, "state": "open"})
        elif action_id == "pull_request.read":
            pr_num = args.get("number", 1)
            return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"number": pr_num, "title": "Fix bug", "state": "open"})
        raise ActionExecutionError(action_id, ErrorCode.NOT_FOUND.value, f"Unknown action '{action_id}'")

    def subscribe_webhook(
        self, connection: IntegrationConnection | None, event_type: str, endpoint: str, secret_store: SecretStore
    ) -> WebhookSubscription:
        sec_id = f"whsec_{uuid4().hex[:8]}"
        secret_store.store(sec_id, {"secret": "github_secret_key"})
        return WebhookSubscription(
            integration_id="intg_mock_github",
            connection_id=connection.connection_id if connection else None,
            event_type=event_type,
            endpoint=endpoint,
            secret_reference=CredentialReference(credential_id=sec_id, credential_type=AuthenticationType.API_KEY, provider_key=self.provider_key),
        )

    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        return True

    def handle_webhook(
        self, headers: dict[str, str], payload: dict[str, Any] | str, subscription: WebhookSubscription, secret_store: SecretStore
    ) -> ExternalEvent:
        data = json.loads(payload) if isinstance(payload, str) else payload
        ev_type = headers.get("x-github-event", data.get("event", "push"))
        return ExternalEvent(source=self.provider_key, integration_id=subscription.integration_id, event_type=f"github.{ev_type}", payload=data)


# =========================================================
# 5. Mock Webhook Provider (with Signature Verification)
# =========================================================

class MockWebhookProvider(BaseMockProvider):
    @property
    def provider_key(self) -> str:
        return "mock_webhook"

    @property
    def name(self) -> str:
        return "Generic Mock Webhook Provider"

    @property
    def category(self) -> IntegrationCategory:
        return IntegrationCategory.OTHER

    def connect(
        self, owner_id: str, auth_data: dict[str, Any], secret_store: SecretStore
    ) -> tuple[IntegrationConnection, CredentialReference]:
        return self._create_connection_and_cred(owner_id, auth_data, secret_store, AuthenticationType.NONE)

    def list_capabilities(self) -> list[IntegrationCapability]:
        return [
            IntegrationCapability(capability_id="webhook.emit", name="webhook.emit", category=IntegrationCategory.OTHER, risk_level=RiskLevel.LOW)
        ]

    def execute_action(
        self,
        connection: IntegrationConnection,
        action_id: str,
        args: dict[str, Any],
        secret_store: SecretStore,
        request_context: dict[str, Any] | None = None,
    ) -> IntegrationResponse:
        req_id = f"req_{uuid4().hex[:12]}"
        return IntegrationResponse(request_id=req_id, status="SUCCESS", data={"emitted": True})

    def subscribe_webhook(
        self, connection: IntegrationConnection | None, event_type: str, endpoint: str, secret_store: SecretStore
    ) -> WebhookSubscription:
        sec_id = f"whsec_{uuid4().hex[:8]}"
        secret_store.store(sec_id, {"secret": "webhook_secret_key_123"})
        return WebhookSubscription(
            integration_id="intg_mock_webhook",
            connection_id=connection.connection_id if connection else None,
            event_type=event_type,
            endpoint=endpoint,
            secret_reference=CredentialReference(credential_id=sec_id, credential_type=AuthenticationType.API_KEY, provider_key=self.provider_key),
        )

    def unsubscribe_webhook(self, subscription: WebhookSubscription, secret_store: SecretStore) -> bool:
        return True

    def handle_webhook(
        self, headers: dict[str, str], payload: dict[str, Any] | str, subscription: WebhookSubscription, secret_store: SecretStore
    ) -> ExternalEvent:
        raw_body = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
        sig_header = headers.get("x-signature") or headers.get("X-Signature")

        if subscription.secret_reference and secret_store.exists(subscription.secret_reference.credential_id):
            secret_data = secret_store.retrieve(subscription.secret_reference.credential_id)
            sec_key = secret_data.get("secret", "").encode("utf-8")
            expected_sig = hmac.new(sec_key, raw_body.encode("utf-8"), hashlib.sha256).hexdigest()

            if sig_header and not hmac.compare_digest(sig_header, expected_sig):
                raise InvalidWebhookSignatureError(subscription.integration_id, "HMAC signature mismatch")

        data = json.loads(raw_body) if isinstance(payload, str) else payload
        ev_type = data.get("event_type", subscription.event_type)

        return ExternalEvent(
            source=self.provider_key,
            integration_id=subscription.integration_id,
            event_type=ev_type,
            payload=data,
        )
