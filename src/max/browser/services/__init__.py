"""Browser Agent services package."""

from max.browser.services.browser_service import BrowserService
from max.browser.services.tool_integration import register_browser_tools

__all__ = [
    "BrowserService",
    "register_browser_tools",
]
