"""Repositories package for Module 20 — Browser Agent."""

from max.browser.repositories.repositories import (
    BrowserAuditRepository,
    BrowserSessionRepository,
    BrowserTabRepository,
)

__all__ = [
    "BrowserSessionRepository",
    "BrowserTabRepository",
    "BrowserAuditRepository",
]
