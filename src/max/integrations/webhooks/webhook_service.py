"""Webhook Ingestion and Event Normalization Framework for Module 29."""

import hashlib
import json
import logging
from typing import Any

from max.integrations.adapters.adapters import Module27NotificationAdapter, Module28SchedulerAdapter
from max.integrations.domain.enums import WebhookProcessingStatus
from max.integrations.domain.exceptions import InvalidWebhookSignatureError
from max.integrations.domain.models import ExternalEvent, WebhookEvent, WebhookSubscription
from max.integrations.repositories.repositories import (
    BaseWebhookEventRepository,
    BaseWebhookSubscriptionRepository,
    MemoryWebhookEventRepository,
    MemoryWebhookSubscriptionRepository,
)
from max.integrations.secrets.secret_store import SecretStore
from max.integrations.services.registry import IntegrationRegistry

logger = logging.getLogger(__name__)


class WebhookService:
    """Ingests, validates, normalizes, deduplicates, and forwards external webhooks."""

    def __init__(
        self,
        registry: IntegrationRegistry,
        secret_store: SecretStore,
        subscription_repo: BaseWebhookSubscriptionRepository | None = None,
        event_repo: BaseWebhookEventRepository | None = None,
        scheduler_adapter: Module28SchedulerAdapter | None = None,
        notification_adapter: Module27NotificationAdapter | None = None,
        max_payload_bytes: int = 1048576,
        replay_window_seconds: float = 300.0,
    ) -> None:
        self._registry = registry
        self._secret_store = secret_store
        self._sub_repo = subscription_repo or MemoryWebhookSubscriptionRepository()
        self._event_repo = event_repo or MemoryWebhookEventRepository()
        self._scheduler_adapter = scheduler_adapter or Module28SchedulerAdapter()
        self._notification_adapter = notification_adapter or Module27NotificationAdapter()
        self._max_payload_bytes = max_payload_bytes
        self._replay_window_seconds = replay_window_seconds

    def subscribe_webhook(
        self, provider_key: str, event_type: str, endpoint: str, connection_id: str | None = None
    ) -> WebhookSubscription:
        """Register a new webhook subscription with a provider."""
        provider = self._registry.get_provider(provider_key)
        conn = None
        if connection_id:
            # Optionally resolve connection if required
            pass

        sub = provider.subscribe_webhook(conn, event_type, endpoint, self._secret_store)
        saved = self._sub_repo.save(sub)
        logger.info("Registered webhook subscription '%s' for integration '%s'", saved.subscription_id, saved.integration_id)
        return saved

    def unsubscribe_webhook(self, subscription_id: str) -> bool:
        """Cancel a webhook subscription."""
        sub = self._sub_repo.get_by_id(subscription_id)
        if not sub:
            return False
        # Derive provider_key from integration_id (format: intg_<key>)
        prov_key = sub.integration_id.replace("intg_", "")
        try:
            provider = self._registry.get_provider(prov_key)
            provider.unsubscribe_webhook(sub, self._secret_store)
        except Exception as exc:
            logger.warning("Unsubscribe provider notice failed: %s", exc)

        return self._sub_repo.delete(subscription_id)

    def ingest_webhook(
        self,
        integration_id_or_key: str,
        headers: dict[str, str],
        payload: dict[str, Any] | str,
    ) -> ExternalEvent:
        """Ingest incoming webhook payload, perform security validation, deduplication, and normalize."""
        raw_str = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)

        # 1. Payload Size Limit Check
        if len(raw_str.encode("utf-8")) > self._max_payload_bytes:
            raise InvalidWebhookSignatureError(integration_id_or_key, "Payload exceeds maximum allowed size.")

        # 2. Deduplication Fingerprint Check
        payload_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        if self._event_repo.exists_by_signature(payload_hash):
            logger.info("Ignored duplicate webhook payload with hash '%s'", payload_hash[:12])
            raise InvalidWebhookSignatureError(integration_id_or_key, "Duplicate webhook event detected.")

        # 3. Resolve Integration & Provider
        intg, _ = self._registry.resolve_action(integration_id_or_key, "webhook.emit") if "mock" in integration_id_or_key else (None, None)
        prov_key = integration_id_or_key.replace("intg_", "")
        provider = self._registry.get_provider(prov_key)

        # Get matching subscription
        subs = self._sub_repo.list_by_integration(f"intg_{prov_key}")
        sub = subs[0] if subs else WebhookSubscription(
            integration_id=f"intg_{prov_key}",
            event_type="generic.event",
            endpoint="/webhooks",
        )

        # 4. Signature & Timestamp Validation (Provider-specific)
        try:
            ext_event = provider.handle_webhook(headers, payload, sub, self._secret_store)
        except Exception as exc:
            whev_failed = WebhookEvent(
                integration_id=f"intg_{prov_key}",
                provider_id=f"prov_{prov_key}",
                event_type="unknown",
                payload_reference=payload_hash,
                signature_status="INVALID",
                processing_status=WebhookProcessingStatus.REJECTED,
            )
            self._event_repo.save(whev_failed)
            raise InvalidWebhookSignatureError(prov_key, str(exc)) from exc

        # 5. Record Validated Webhook Event
        whev = WebhookEvent(
            integration_id=ext_event.integration_id,
            provider_id=f"prov_{prov_key}",
            event_type=ext_event.event_type,
            payload_reference=payload_hash,
            signature_status="VALID",
            processing_status=WebhookProcessingStatus.NORMALIZED,
        )
        self._event_repo.save(whev)

        # 6. Forward Normalized ExternalEvent to Module 28 Scheduler
        self._scheduler_adapter.emit_external_event(
            event_type=ext_event.event_type,
            source=ext_event.source,
            payload=ext_event.payload,
        )

        whev.processing_status = WebhookProcessingStatus.EMITTED
        self._event_repo.save(whev)

        logger.info("Successfully ingested & normalized webhook event '%s' from '%s'", ext_event.event_type, prov_key)
        return ext_event
