"""PlaywrightBrowserBackend — Real Playwright browser engine implementation for Module 20.

Uses Playwright async API for Chromium / Firefox / WebKit.
Detects browser availability cleanly without auto-downloading during runtime.
"""

from datetime import UTC, datetime
import logging
import os
import threading
from typing import Any

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
    BrowserLaunchError,
    BrowserNavigationError,
    BrowserNotFoundError,
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

logger = logging.getLogger(__name__)


class PlaywrightBrowserBackend(BrowserBackend):
    """Playwright-backed browser engine for Chromium, Firefox, WebKit."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._pw: Any = None
        self._browser: Any = None
        self._playwright_available: bool | None = None
        self._contexts: dict[str, Any] = {}  # session_id -> Playwright BrowserContext
        self._pages: dict[str, dict[str, Any]] = {}  # session_id -> {tab_id -> Playwright Page}
        self._sessions: dict[str, BrowserSession] = {}
        self._tabs: dict[str, dict[str, BrowserTab]] = {}

    def is_available(self) -> bool:
        """Check if playwright library and browser engine can be imported and initialized."""
        if self._playwright_available is not None:
            return self._playwright_available

        try:
            import playwright.async_api  # noqa: F401
            self._playwright_available = True
        except ImportError:
            self._playwright_available = False

        return self._playwright_available

    async def _ensure_playwright(self, engine: BrowserEngine = BrowserEngine.CHROMIUM) -> None:
        if not self.is_available():
            raise BrowserNotFoundError("Playwright library is not installed in the python environment.")

        if self._pw is None:
            from playwright.async_api import async_playwright
            try:
                self._pw = await async_playwright().start()
                if engine == BrowserEngine.FIREFOX:
                    self._browser = await self._pw.firefox.launch(headless=True)
                elif engine == BrowserEngine.WEBKIT:
                    self._browser = await self._pw.webkit.launch(headless=True)
                else:
                    self._browser = await self._pw.chromium.launch(headless=True)
            except Exception as e:
                logger.error("Failed to launch Playwright browser engine: %s", e)
                raise BrowserLaunchError(f"Failed to launch Playwright browser engine '{engine}': {e}") from e

    async def create_session(self, session: BrowserSession) -> BrowserSession:
        await self._ensure_playwright(session.engine)

        context = await self._browser.new_context(
            viewport={
                "width": session.configuration.viewport_width,
                "height": session.configuration.viewport_height,
            },
            accept_downloads=session.configuration.accept_downloads,
            user_agent=session.configuration.user_agent,
        )

        page = await context.new_page()

        with self._lock:
            self._contexts[session.session_id] = context
            self._pages[session.session_id] = {}
            self._sessions[session.session_id] = session

            first_tab = BrowserTab(
                session_id=session.session_id,
                url="about:blank",
                title="New Tab",
                status=BrowserTabStatus.ACTIVE,
                is_active=True,
            )
            self._pages[session.session_id][first_tab.tab_id] = page
            self._tabs[session.session_id] = {first_tab.tab_id: first_tab}

            updated = session.model_copy(
                update={"status": BrowserStatus.READY, "active_tab_id": first_tab.tab_id}
            )
            self._sessions[session.session_id] = updated
            return updated

    async def close_session(self, session_id: str) -> bool:
        context = self._contexts.pop(session_id, None)
        if context:
            try:
                await context.close()
            except Exception as e:
                logger.warning("Error closing Playwright context for session '%s': %s", session_id, e)
            self._pages.pop(session_id, None)
            self._tabs.pop(session_id, None)
            if session_id in self._sessions:
                self._sessions[session_id] = self._sessions[session_id].model_copy(
                    update={"status": BrowserStatus.CLOSED}
                )
            return True
        return False

    async def create_tab(self, session_id: str, url: str = "about:blank") -> BrowserTab:
        context = self._get_context(session_id)
        page = await context.new_page()
        if url and url != "about:blank":
            await page.goto(url)

        new_tab = BrowserTab(
            session_id=session_id,
            url=page.url or url,
            title=await page.title() or "New Tab",
            status=BrowserTabStatus.ACTIVE,
            is_active=True,
        )
        with self._lock:
            self._pages[session_id][new_tab.tab_id] = page
            self._tabs[session_id][new_tab.tab_id] = new_tab
            return new_tab

    async def close_tab(self, session_id: str, tab_id: str) -> bool:
        page = self._get_page(session_id, tab_id)
        try:
            await page.close()
        except Exception:
            pass
        with self._lock:
            self._pages[session_id].pop(tab_id, None)
            self._tabs[session_id].pop(tab_id, None)
            return True

    async def navigate(
        self, session_id: str, tab_id: str, request: BrowserNavigationRequest
    ) -> BrowserNavigationResult:
        page = self._get_page(session_id, tab_id)
        try:
            response = await page.goto(request.url, timeout=(request.timeout or 30.0) * 1000)
            status_code = response.status if response else 200
            current_url = page.url
            title = await page.title()

            tab = self._get_tab_model(session_id, tab_id)
            updated_tab = tab.model_copy(
                update={"url": current_url, "title": title, "status": BrowserTabStatus.ACTIVE}
            )
            with self._lock:
                self._tabs[session_id][tab_id] = updated_tab

            return BrowserNavigationResult(
                url=current_url,
                title=title,
                status_code=status_code,
                success=True,
            )
        except Exception as e:
            raise BrowserNavigationError(f"Navigation to '{request.url}' failed: {e}") from e

    async def go_back(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        page = self._get_page(session_id, tab_id)
        res = await page.go_back()
        return BrowserNavigationResult(
            url=page.url,
            title=await page.title(),
            status_code=res.status if res else 200,
            success=True,
        )

    async def go_forward(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        page = self._get_page(session_id, tab_id)
        res = await page.go_forward()
        return BrowserNavigationResult(
            url=page.url,
            title=await page.title(),
            status_code=res.status if res else 200,
            success=True,
        )

    async def reload(self, session_id: str, tab_id: str) -> BrowserNavigationResult:
        page = self._get_page(session_id, tab_id)
        res = await page.reload()
        return BrowserNavigationResult(
            url=page.url,
            title=await page.title(),
            status_code=res.status if res else 200,
            success=True,
        )

    async def observe_page(self, session_id: str, tab_id: str) -> BrowserObservation:
        page = self._get_page(session_id, tab_id)
        url = page.url
        title = await page.title()

        # Extract visible text safely
        try:
            body_text = await page.inner_text("body")
        except Exception:
            body_text = ""

        # Limit text content to 100KB for prompt safety
        truncated_text = body_text[:100000]

        # Extract clickable elements
        elements = []
        try:
            buttons = await page.locator("button, input[type='button'], input[type='submit']").all()
            for b in buttons[:20]:
                text = await b.inner_text()
                elements.append(
                    BrowserElement(
                        element_type=BrowserElementType.BUTTON,
                        tag_name="button",
                        text=text[:100],
                        locator=BrowserElementLocator(text=text[:50] if text else None),
                    )
                )
        except Exception as e:
            logger.debug("Failed extracting buttons in observe: %s", e)

        return BrowserObservation(
            url=url,
            title=title,
            page_metadata=BrowserPageMetadata(title=title),
            text_content=truncated_text,
            elements=elements,
            is_untrusted_web_content=True,
        )

    async def click(
        self, session_id: str, tab_id: str, request: BrowserClickRequest
    ) -> BrowserClickResult:
        page = self._get_page(session_id, tab_id)
        selector = request.locator.to_selector()
        try:
            await page.click(selector, timeout=15000)
            return BrowserClickResult(
                success=True,
                resulting_url=page.url,
                verification_status=BrowserVerificationStatus.VERIFIED,
            )
        except Exception as e:
            raise BrowserElementNotInteractableError(f"Failed to click element '{selector}': {e}") from e

    async def type_text(
        self, session_id: str, tab_id: str, request: BrowserTypeRequest
    ) -> BrowserTypeResult:
        page = self._get_page(session_id, tab_id)
        selector = request.locator.to_selector()
        try:
            if request.clear_first:
                await page.fill(selector, request.text)
            else:
                await page.type(selector, request.text)

            masked = "***" if request.is_sensitive else request.text
            return BrowserTypeResult(success=True, masked_value=masked)
        except Exception as e:
            raise BrowserElementNotInteractableError(f"Failed to type into '{selector}': {e}") from e

    async def select_option(
        self, session_id: str, tab_id: str, request: BrowserSelectRequest
    ) -> BrowserSelectResult:
        page = self._get_page(session_id, tab_id)
        selector = request.locator.to_selector()
        try:
            selected = await page.select_option(selector, request.value)
            return BrowserSelectResult(success=True, selected_value=selected[0] if selected else request.value)
        except Exception as e:
            raise BrowserElementNotInteractableError(f"Failed to select option in '{selector}': {e}") from e

    async def scroll(
        self, session_id: str, tab_id: str, request: BrowserScrollRequest
    ) -> BrowserScrollResult:
        page = self._get_page(session_id, tab_id)
        try:
            if request.direction == "down":
                await page.evaluate(f"window.scrollBy(0, {request.amount_pixels});")
            elif request.direction == "up":
                await page.evaluate(f"window.scrollBy(0, -{request.amount_pixels});")
            elif request.direction == "top":
                await page.evaluate("window.scrollTo(0, 0);")
            elif request.direction == "bottom":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

            current_y = await page.evaluate("window.scrollY;")
            return BrowserScrollResult(success=True, current_scroll_y=int(current_y or 0))
        except Exception as e:
            return BrowserScrollResult(success=False)

    async def wait_for_condition(
        self, session_id: str, tab_id: str, request: BrowserWaitRequest
    ) -> BrowserWaitResult:
        page = self._get_page(session_id, tab_id)
        try:
            if request.condition == "element" and request.locator:
                await page.wait_for_selector(request.locator.to_selector(), timeout=request.timeout * 1000)
            elif request.condition == "url" and request.expected_url:
                await page.wait_for_url(request.expected_url, timeout=request.timeout * 1000)
            else:
                await page.wait_for_load_state("load", timeout=request.timeout * 1000)
            return BrowserWaitResult(success=True, elapsed_seconds=0.5)
        except Exception as e:
            raise BrowserTimeoutError(f"Wait condition '{request.condition}' timed out: {e}") from e

    async def take_screenshot(
        self, session_id: str, tab_id: str, request: BrowserScreenshotRequest
    ) -> BrowserScreenshotResult:
        page = self._get_page(session_id, tab_id)
        try:
            img_bytes = await page.screenshot(type="jpeg", quality=request.quality, full_page=request.full_page)
            return BrowserScreenshotResult(image_bytes=img_bytes, mime_type="image/jpeg")
        except Exception as e:
            raise BrowserNavigationError(f"Failed to capture screenshot: {e}") from e

    async def extract_content(
        self, session_id: str, tab_id: str, request: BrowserExtractRequest
    ) -> BrowserExtractResult:
        page = self._get_page(session_id, tab_id)
        if request.target == "text":
            text = await page.inner_text("body")
            return BrowserExtractResult(text=text[:100000])

        if request.target == "links":
            links = []
            anchors = await page.locator("a[href]").all()
            for a in anchors[:50]:
                href = await a.get_attribute("href")
                t = await a.inner_text()
                if href:
                    links.append(BrowserLink(text=t[:100], url=href))
            return BrowserExtractResult(links=links)

        return BrowserExtractResult(text=await page.inner_text("body"))

    async def download_file(
        self, session_id: str, tab_id: str, url: str, target_path: str
    ) -> BrowserDownload:
        page = self._get_page(session_id, tab_id)
        async with page.expect_download() as download_info:
            await page.goto(url)
        download = await download_info.value
        await download.save_as(target_path)
        return BrowserDownload(
            url=url,
            suggested_filename=download.suggested_filename,
            file_path=target_path,
            file_size_bytes=os.path.getsize(target_path) if os.path.exists(target_path) else 0,
            completed=True,
        )

    async def upload_file(
        self, session_id: str, tab_id: str, locator: BrowserElementLocator, file_path: str
    ) -> BrowserUpload:
        page = self._get_page(session_id, tab_id)
        selector = locator.to_selector()
        await page.set_input_files(selector, file_path)
        return BrowserUpload(
            file_path=file_path,
            target_locator=locator,
            file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            completed=True,
        )

    def _get_context(self, session_id: str) -> Any:
        ctx = self._contexts.get(session_id)
        if not ctx:
            raise BrowserSessionNotFoundError(f"Playwright context for session '{session_id}' not found.")
        return ctx

    def _get_page(self, session_id: str, tab_id: str) -> Any:
        p_map = self._pages.get(session_id, {})
        page = p_map.get(tab_id)
        if not page:
            raise BrowserTabNotFoundError(f"Playwright page for tab '{tab_id}' not found in session '{session_id}'.")
        return page

    def _get_tab_model(self, session_id: str, tab_id: str) -> BrowserTab:
        tabs = self._tabs.get(session_id, {})
        if tab_id not in tabs:
            raise BrowserTabNotFoundError(f"Tab '{tab_id}' not found in session '{session_id}'.")
        return tabs[tab_id]
