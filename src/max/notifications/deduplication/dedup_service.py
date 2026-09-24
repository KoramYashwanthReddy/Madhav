"""Deduplication service for Module 27 — Notification System."""

from __future__ import annotations

import hashlib
import time

from max.notifications.domain.models import Notification


class NotificationDeduplicationService:
    """Provides deterministic deduplication over sliding time windows."""

    def __init__(self, window_seconds: float = 30.0) -> None:
        self.window_seconds = window_seconds
        self._seen_keys: dict[str, float] = {}

    def compute_dedup_key(self, notification: Notification) -> str:
        """Compute deterministic SHA-256 deduplication key."""
        if notification.deduplication_key:
            return notification.deduplication_key

        raw = f"{notification.recipient.recipient_id}:{notification.category.value}:{notification.content.title}:{notification.source.source_id}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def is_duplicate(self, notification: Notification) -> bool:
        """Check if notification is a duplicate within the deduplication window."""
        key = self.compute_dedup_key(notification)
        now = time.monotonic()

        # Clean expired keys
        self._seen_keys = {k: ts for k, ts in self._seen_keys.items() if now - ts < self.window_seconds}

        if key in self._seen_keys:
            return True

        self._seen_keys[key] = now
        return False
