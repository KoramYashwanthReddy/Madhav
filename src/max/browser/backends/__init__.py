"""Backends package for Module 20 — Browser Agent."""

from max.browser.backends.base import BrowserBackend
from max.browser.backends.mock import MockBrowserBackend
from max.browser.backends.playwright import PlaywrightBrowserBackend

__all__ = [
    "BrowserBackend",
    "MockBrowserBackend",
    "PlaywrightBrowserBackend",
]
