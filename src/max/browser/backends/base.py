"""Abstract base class for Browser Agent backends (Module 20)."""

from abc import ABC, abstractmethod
from typing import Any

from max.browser.domain.models import (
    BrowserActionRequest,
    BrowserActionResult,
    BrowserClickRequest,
    BrowserClickResult,
    BrowserDownload,
    BrowserElement,
    BrowserElementLocator,
    BrowserExtractRequest,
    BrowserExtractResult,
    BrowserNavigationRequest,
    BrowserNavigationResult,
    BrowserObservation,
    BrowserScreenshotRequest,
    BrowserScreenshotResult,
    BrowserScrollRequest,
    BrowserScrollResult,
    BrowserSelectRequest,
    BrowserSelectResult,
    BrowserSession,
    BrowserTab,
    BrowserTypeRequest,
    BrowserTypeResult,
    BrowserUpload,
    BrowserWaitRequest,
    BrowserWaitResult,
)


class BrowserBackend(ABC):
    """Abstract interface all Browser backends (Playwright, Mock) must implement."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this browser backend engine is installed and ready."""

    @abstractmethod
    async def create_session(self, session: BrowserSession) -> BrowserSession:
        """Initialize a new isolated browser context/session."""

    @abstractmethod
    async def close_session(self, session_id: str) -> bool:
        """Close an active browser session and cleanup its resources."""

    @abstractmethod
    async def create_tab(self, session_id: str, url: str = "about:blank") -> BrowserTab:
        """Create a new tab within a session."""

    @abstractmethod
    async def close_tab(self, session_id: str, tab_id: str) -> bool:
        """Close a specific tab."""

    @abstractmethod
    async def navigate(
        self, session_id: str, tab_id: str, request: BrowserNavigationRequest
    ) -> BrowserNavigationResult:
        """Navigate tab to URL."""

    @abstractmethod
    async def go_back(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        """Navigate backward in history."""

    @abstractmethod
    async def go_forward(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        """Navigate forward in history."""

    @abstractmethod
    async def reload(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        """Reload page in tab."""

    @abstractmethod
    async def observe_page(self, session_id: str, tab_id: str) -> BrowserObservation:
        """Extract structured page observation snapshot."""

    @abstractmethod
    async def click(
        self, session_id: str, tab_id: str, request: BrowserClickRequest
    ) -> BrowserClickResult:
        """Click element in page."""

    @abstractmethod
    async def type_text(
        self, session_id: str, tab_id: str, request: BrowserTypeRequest
    ) -> BrowserTypeResult:
        """Type text into field."""

    @abstractmethod
    async def select_option(
        self, session_id: str, tab_id: str, request: BrowserSelectRequest
    ) -> BrowserSelectResult:
        """Select drop-down option."""

    @abstractmethod
    async def scroll(
        self, session_id: str, tab_id: str, request: BrowserScrollRequest
    ) -> BrowserScrollResult:
        """Scroll page."""

    @abstractmethod
    async def wait_for_condition(
        self, session_id: str, tab_id: str, request: BrowserWaitRequest
    ) -> BrowserWaitResult:
        """Wait for load state, element, or URL condition."""

    @abstractmethod
    async def take_screenshot(
        self, session_id: str, tab_id: str, request: BrowserScreenshotRequest
    ) -> BrowserScreenshotResult:
        """Capture screenshot."""

    @abstractmethod
    async def extract_content(
        self, session_id: str, tab_id: str, request: BrowserExtractRequest
    ) -> BrowserExtractResult:
        """Extract text, links, or forms from page."""

    @abstractmethod
    async def download_file(
        self, session_id: str, tab_id: str, url: str, target_path: str
    ) -> BrowserDownload:
        """Download file."""

    @abstractmethod
    async def upload_file(
        self, session_id: str, tab_id: str, locator: BrowserElementLocator, file_path: str
    ) -> BrowserUpload:
        """Upload file."""
