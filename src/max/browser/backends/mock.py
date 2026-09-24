"""MockBrowserBackend — deterministic in-memory browser backend for testing.

Never launches a real browser binary, never makes external network calls.
Simulates browser sessions, tabs, navigation, observations, DOM elements, clicks,
typing, form submissions, screenshots, downloads, and uploads.
"""

from datetime import UTC, datetime
import os
import threading
from typing import Any
import uuid

from max.browser.backends.base import BrowserBackend
from max.browser.domain.enums import (
    BrowserActionStatus,
    BrowserActionType,
    BrowserElementType,
    BrowserEngine,
    BrowserStatus,
    BrowserTabStatus,
    BrowserType,
    BrowserVerificationStatus,
)
from max.browser.domain.exceptions import (
    BrowserElementNotFoundError,
    BrowserNavigationError,
    BrowserSessionNotFoundError,
    BrowserTabNotFoundError,
    BrowserTimeoutError,
)
from max.browser.domain.models import (
    BrowserClickRequest,
    BrowserClickResult,
    BrowserDownload,
    BrowserElement,
    BrowserElementLocator,
    BrowserExtractRequest,
    BrowserExtractResult,
    BrowserForm,
    BrowserInput,
    BrowserLink,
    BrowserNavigationRequest,
    BrowserNavigationResult,
    BrowserObservation,
    BrowserPage,
    BrowserPageMetadata,
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


class MockBrowserBackend(BrowserBackend):
    """Deterministic in-memory mock browser backend."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._available: bool = True
        self._sessions: dict[str, BrowserSession] = {}
        self._tabs: dict[str, dict[str, BrowserTab]] = {}  # session_id -> {tab_id -> BrowserTab}
        self._history: dict[str, list[str]] = {}  # tab_id -> list of URLs
        self._history_index: dict[str, int] = {}  # tab_id -> current index in history
        self._mock_pages: dict[str, BrowserObservation] = {}  # url -> custom observation

        # Test failure triggers
        self.should_fail_navigation: bool = False
        self.should_timeout: bool = False
        self.should_fail_verification: bool = False

    def is_available(self) -> bool:
        return self._available

    def set_available(self, available: bool) -> None:
        with self._lock:
            self._available = available

    def register_mock_page(self, url: str, observation: BrowserObservation) -> None:
        """Register a canned page observation for testing a specific URL."""
        with self._lock:
            self._mock_pages[url] = observation

    async def create_session(self, session: BrowserSession) -> BrowserSession:
        with self._lock:
            active_session = session.model_copy(update={"status": BrowserStatus.READY})
            self._sessions[session.session_id] = active_session
            self._tabs[session.session_id] = {}

            # Create default first tab
            first_tab = BrowserTab(
                session_id=session.session_id,
                url="about:blank",
                title="New Tab",
                status=BrowserTabStatus.ACTIVE,
                is_active=True,
            )
            self._tabs[session.session_id][first_tab.tab_id] = first_tab
            self._history[first_tab.tab_id] = ["about:blank"]
            self._history_index[first_tab.tab_id] = 0

            updated = active_session.model_copy(update={"active_tab_id": first_tab.tab_id})
            self._sessions[session.session_id] = updated
            return updated

    async def close_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._sessions:
                sess = self._sessions[session_id]
                self._sessions[session_id] = sess.model_copy(update={"status": BrowserStatus.CLOSED})
                if session_id in self._tabs:
                    del self._tabs[session_id]
                return True
            return False

    async def create_tab(self, session_id: str, url: str = "about:blank") -> BrowserTab:
        with self._lock:
            if session_id not in self._sessions:
                raise BrowserSessionNotFoundError(f"Session '{session_id}' not found.")

            # Deactivate other tabs
            for tid, tab in self._tabs[session_id].items():
                self._tabs[session_id][tid] = tab.model_copy(update={"is_active": False})

            new_tab = BrowserTab(
                session_id=session_id,
                url=url,
                title="New Tab",
                status=BrowserTabStatus.ACTIVE,
                is_active=True,
            )
            self._tabs[session_id][new_tab.tab_id] = new_tab
            self._history[new_tab.tab_id] = [url]
            self._history_index[new_tab.tab_id] = 0

            self._sessions[session_id] = self._sessions[session_id].model_copy(
                update={"active_tab_id": new_tab.tab_id}
            )
            return new_tab

    async def close_tab(self, session_id: str, tab_id: str) -> bool:
        with self._lock:
            if session_id in self._tabs and tab_id in self._tabs[session_id]:
                del self._tabs[session_id][tab_id]
                if tab_id in self._history:
                    del self._history[tab_id]
                return True
            return False

    async def navigate(
        self, session_id: str, tab_id: str, request: BrowserNavigationRequest
    ) -> BrowserNavigationResult:
        if self.should_timeout:
            raise BrowserTimeoutError("Navigation timed out in MockBrowserBackend.")
        if self.should_fail_navigation:
            raise BrowserNavigationError(f"Simulated navigation failure for URL '{request.url}'.")

        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            target_url = request.url

            # Update history
            h_list = self._history.setdefault(tab_id, [])
            idx = self._history_index.get(tab_id, 0)
            h_list = h_list[: idx + 1]
            h_list.append(target_url)
            self._history[tab_id] = h_list
            self._history_index[tab_id] = len(h_list) - 1

            title = f"Page — {target_url}"
            if target_url in self._mock_pages:
                title = self._mock_pages[target_url].title

            # Update tab state
            updated_tab = tab.model_copy(
                update={
                    "url": target_url,
                    "title": title,
                    "status": BrowserTabStatus.ACTIVE,
                    "last_activity": datetime.now(UTC),
                }
            )
            self._tabs[session_id][tab_id] = updated_tab

            return BrowserNavigationResult(
                url=target_url,
                title=title,
                status_code=200,
                success=True,
            )

    async def go_back(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            idx = self._history_index.get(tab_id, 0)
            h_list = self._history.get(tab_id, [tab.url])
            if idx > 0:
                idx -= 1
                self._history_index[tab_id] = idx
                target_url = h_list[idx]
                return await self.navigate(session_id, tab_id, BrowserNavigationRequest(url=target_url))
            return BrowserNavigationResult(url=tab.url, title=tab.title, success=True)

    async def go_forward(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            idx = self._history_index.get(tab_id, 0)
            h_list = self._history.get(tab_id, [tab.url])
            if idx < len(h_list) - 1:
                idx += 1
                self._history_index[tab_id] = idx
                target_url = h_list[idx]
                return await self.navigate(session_id, tab_id, BrowserNavigationRequest(url=target_url))
            return BrowserNavigationResult(url=tab.url, title=tab.title, success=True)

    async def reload(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            return await self.navigate(session_id, tab_id, BrowserNavigationRequest(url=tab.url))

    async def observe_page(self, session_id: str, tab_id: str) -> BrowserObservation:
        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            url = tab.url

            if url in self._mock_pages:
                return self._mock_pages[url]

            # Generate default structured observation for mock
            btn_elem = BrowserElement(
                element_type=BrowserElementType.BUTTON,
                tag_name="button",
                text="Submit",
                locator=BrowserElementLocator(css="#submit-btn", text="Submit"),
            )
            input_elem = BrowserElement(
                element_type=BrowserElementType.INPUT,
                tag_name="input",
                text="",
                value="",
                locator=BrowserElementLocator(css="#username-input", name="username"),
            )

            return BrowserObservation(
                url=url,
                title=tab.title,
                page_metadata=BrowserPageMetadata(title=tab.title),
                text_content=f"Mock page content for {url}. Welcome to Max Browser Agent.",
                elements=[btn_elem, input_elem],
                links=[BrowserLink(text="Home", url="https://example.com")],
                forms=[
                    BrowserForm(
                        action_url="/login",
                        method="POST",
                        inputs=[
                            BrowserInput(name="username", input_type="text"),
                            BrowserInput(name="password", input_type="password", is_sensitive=True),
                        ],
                    )
                ],
                is_untrusted_web_content=True,
            )

    async def click(
        self, session_id: str, tab_id: str, request: BrowserClickRequest
    ) -> BrowserClickResult:
        if self.should_timeout:
            raise BrowserTimeoutError("Click operation timed out.")
        with self._lock:
            tab = self._get_tab(session_id, tab_id)
            if self.should_fail_verification:
                return BrowserClickResult(
                    success=True,
                    resulting_url=tab.url,
                    verification_status=BrowserVerificationStatus.ACTION_COMPLETED_UNVERIFIED,
                )
            return BrowserClickResult(
                success=True,
                resulting_url=tab.url,
                verification_status=BrowserVerificationStatus.VERIFIED,
            )

    async def type_text(
        self, session_id: str, tab_id: str, request: BrowserTypeRequest
    ) -> BrowserTypeResult:
        if self.should_timeout:
            raise BrowserTimeoutError("Type operation timed out.")
        with self._lock:
            masked = "***" if request.is_sensitive else request.text
            return BrowserTypeResult(success=True, masked_value=masked)

    async def select_option(
        self, session_id: str, tab_id: str, request: BrowserSelectRequest
    ) -> BrowserSelectResult:
        with self._lock:
            return BrowserSelectResult(success=True, selected_value=request.value)

    async def scroll(
        self, session_id: str, tab_id: str, request: BrowserScrollRequest
    ) -> BrowserScrollResult:
        with self._lock:
            return BrowserScrollResult(success=True, current_scroll_y=request.amount_pixels)

    async def wait_for_condition(
        self, session_id: str, tab_id: str, request: BrowserWaitRequest
    ) -> BrowserWaitResult:
        if self.should_timeout:
            raise BrowserTimeoutError("Wait condition timed out.")
        return BrowserWaitResult(success=True, elapsed_seconds=0.1)

    async def take_screenshot(
        self, session_id: str, tab_id: str, request: BrowserScreenshotRequest
    ) -> BrowserScreenshotResult:
        mock_jpeg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb"
        return BrowserScreenshotResult(image_bytes=mock_jpeg, mime_type="image/jpeg")

    async def extract_content(
        self, session_id: str, tab_id: str, request: BrowserExtractRequest
    ) -> BrowserExtractResult:
        obs = await self.observe_page(session_id, tab_id)
        if request.target == "links":
            return BrowserExtractResult(links=obs.links)
        if request.target == "forms":
            return BrowserExtractResult(forms=obs.forms)
        return BrowserExtractResult(text=obs.text_content)

    async def download_file(
        self, session_id: str, tab_id: str, url: str, target_path: str
    ) -> BrowserDownload:
        # Write small mock file
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(b"Mock downloaded file content")

        return BrowserDownload(
            url=url,
            suggested_filename=os.path.basename(target_path),
            file_path=target_path,
            file_size_bytes=28,
            completed=True,
        )

    async def upload_file(
        self, session_id: str, tab_id: str, locator: BrowserElementLocator, file_path: str
    ) -> BrowserUpload:
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 100
        return BrowserUpload(
            file_path=file_path,
            target_locator=locator,
            file_size_bytes=file_size,
            completed=True,
        )

    def _get_tab(self, session_id: str, tab_id: str) -> BrowserTab:
        if session_id not in self._sessions or self._sessions[session_id].status == BrowserStatus.CLOSED:
            raise BrowserSessionNotFoundError(f"Session '{session_id}' is closed or not found.")
        tabs = self._tabs.get(session_id, {})
        if tab_id not in tabs or tabs[tab_id].status == BrowserTabStatus.CLOSED:
            raise BrowserTabNotFoundError(f"Tab '{tab_id}' is closed or not found in session '{session_id}'.")
        return tabs[tab_id]
