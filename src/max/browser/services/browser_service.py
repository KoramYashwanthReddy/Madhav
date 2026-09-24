"""BrowserService — Primary Facade Service for Module 20 Browser Agent.

Orchestrates browser sessions, tab management, navigation, structured page observation,
element interaction (click, type, select, scroll), content extraction, screenshots,
downloads, uploads, post-action state verification, and audit trace logging.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from max.browser.backends.base import BrowserBackend
from max.browser.domain.enums import (
    BrowserActionType,
    BrowserAuditEventType,
    BrowserStatus,
)
from max.browser.domain.exceptions import (
    BrowserError,
    BrowserSessionNotFoundError,
    BrowserSubsystemDisabledError,
    BrowserTabNotFoundError,
)
from max.browser.domain.models import (
    BrowserAuditEvent,
    BrowserClickRequest,
    BrowserClickResult,
    BrowserDownload,
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
from max.browser.repositories.repositories import (
    BrowserAuditRepository,
    BrowserSessionRepository,
    BrowserTabRepository,
)
from max.browser.security.browser_policy import BrowserPolicyService
from max.config.sections import BrowserSettings

logger = logging.getLogger(__name__)


class BrowserService:
    """Primary facade service for Browser Agent operations."""

    def __init__(
        self,
        backend: BrowserBackend,
        settings: BrowserSettings | None = None,
        session_repo: BrowserSessionRepository | None = None,
        tab_repo: BrowserTabRepository | None = None,
        audit_repo: BrowserAuditRepository | None = None,
        policy_service: BrowserPolicyService | None = None,
    ) -> None:
        self.backend = backend
        self.settings = settings or BrowserSettings()
        self.session_repo = session_repo or BrowserSessionRepository()
        self.tab_repo = tab_repo or BrowserTabRepository()
        self.audit_repo = audit_repo or BrowserAuditRepository()
        self.policy_service = policy_service or BrowserPolicyService(settings=self.settings)

    async def create_session(
        self, owner_id: str = "system", metadata: dict[str, Any] | None = None
    ) -> BrowserSession:
        """Create and initialize a new isolated browser session."""
        if not self.settings.enabled:
            raise BrowserSubsystemDisabledError("Browser Agent subsystem is disabled.")

        if self.session_repo.count_active() >= self.settings.max_sessions:
            raise BrowserError(
                f"Maximum concurrent active browser session limit ({self.settings.max_sessions}) reached."
            )

        new_sess = BrowserSession(owner_id=owner_id, metadata=metadata or {})
        session = await self.backend.create_session(new_sess)
        self.session_repo.save(session)

        # Sync tab
        tabs = self.tab_repo.list_tabs(session.session_id)
        if not tabs and session.active_tab_id:
            first_tab = BrowserTab(
                tab_id=session.active_tab_id,
                session_id=session.session_id,
                url="about:blank",
            )
            self.tab_repo.save(first_tab)

        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.SESSION_CREATED,
                session_id=session.session_id,
                owner_id=owner_id,
            )
        )
        return session

    async def close_session(self, session_id: str, owner_id: str = "system") -> bool:
        """Close an active browser session."""
        sess = self.session_repo.get(session_id)
        if not sess:
            return False

        if sess.owner_id != owner_id and owner_id != "system":
            raise BrowserError("Unauthorized to close another owner's browser session.")

        res = await self.backend.close_session(session_id)
        if res:
            self.session_repo.save(sess.model_copy(update={"status": BrowserStatus.CLOSED}))
            self.tab_repo.clear_session(session_id)
            self.audit_repo.record(
                BrowserAuditEvent(
                    event_type=BrowserAuditEventType.SESSION_CLOSED,
                    session_id=session_id,
                    owner_id=owner_id,
                )
            )
        return res

    async def create_tab(self, session_id: str, url: str = "about:blank") -> BrowserTab:
        """Create a new tab in an active session."""
        self._get_session(session_id)
        existing_tabs = self.tab_repo.list_tabs(session_id, active_only=True)
        if len(existing_tabs) >= self.settings.max_tabs_per_session:
            raise BrowserError(
                f"Maximum tab limit per session ({self.settings.max_tabs_per_session}) reached."
            )

        if url and url != "about:blank":
            self.policy_service.validate_url(url)

        tab = await self.backend.create_tab(session_id, url)
        self.tab_repo.save(tab)

        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.TAB_CREATED,
                session_id=session_id,
                tab_id=tab.tab_id,
                url=url,
            )
        )
        return tab

    async def list_tabs(self, session_id: str) -> list[BrowserTab]:
        """List active tabs in a session."""
        self._get_session(session_id)
        return self.tab_repo.list_tabs(session_id, active_only=True)

    async def switch_tab(self, session_id: str, tab_id: str) -> BrowserTab:
        """Switch active tab in a session."""
        sess = self._get_session(session_id)
        tab = self.tab_repo.get(session_id, tab_id)
        if not tab:
            raise BrowserTabNotFoundError(f"Tab '{tab_id}' not found in session '{session_id}'.")

        # Deactivate others
        for t in self.tab_repo.list_tabs(session_id):
            if t.tab_id != tab_id:
                self.tab_repo.save(t.model_copy(update={"is_active": False}))

        active_tab = tab.model_copy(update={"is_active": True})
        self.tab_repo.save(active_tab)
        self.session_repo.save(sess.model_copy(update={"active_tab_id": tab_id}))
        return active_tab

    async def close_tab(self, session_id: str, tab_id: str) -> bool:
        """Close a specific tab."""
        self._get_session(session_id)
        res = await self.backend.close_tab(session_id, tab_id)
        if res:
            self.tab_repo.delete(session_id, tab_id)
            self.audit_repo.record(
                BrowserAuditEvent(
                    event_type=BrowserAuditEventType.TAB_CLOSED,
                    session_id=session_id,
                    tab_id=tab_id,
                )
            )
        return res

    async def navigate(
        self,
        session_id: str,
        url: str,
        tab_id: str | None = None,
        timeout: float | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> BrowserNavigationResult:
        """Navigate to a target URL after security validation and permission checks."""
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        # Policy & Permission validation
        self.policy_service.validate_action(
            action_type=BrowserActionType.NAVIGATE,
            target_url=url,
            owner_id=owner_id,
            agent_id=agent_id,
        )

        req = BrowserNavigationRequest(url=url, tab_id=target_tab_id, timeout=timeout)
        datetime.now(UTC)

        res = await self.backend.navigate(session_id, target_tab_id, req)

        # Update tab repo
        tab = self.tab_repo.get(session_id, target_tab_id)
        if tab:
            self.tab_repo.save(tab.model_copy(update={"url": res.url, "title": res.title}))

        # Audit
        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.NAVIGATED,
                session_id=session_id,
                tab_id=target_tab_id,
                url=res.url,
                owner_id=owner_id,
                agent_id=agent_id,
            )
        )
        return res

    async def go_back(self, session_id: str, tab_id: str | None = None) -> BrowserNavigationResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        return await self.backend.go_back(session_id, target_tab_id)

    async def go_forward(self, session_id: str, tab_id: str | None = None) -> BrowserNavigationResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        return await self.backend.go_forward(session_id, target_tab_id)

    async def reload(self, session_id: str, tab_id: str | None = None) -> BrowserNavigationResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        return await self.backend.reload(session_id, target_tab_id)

    async def observe_page(
        self, session_id: str, tab_id: str | None = None
    ) -> BrowserObservation:
        """Observe current page state, returning sanitized, bounded observation object."""
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        raw_obs = await self.backend.observe_page(session_id, target_tab_id)
        sanitized_obs = self.policy_service.sanitize_observation(raw_obs)

        if sanitized_obs.prompt_injection_warning:
            self.audit_repo.record(
                BrowserAuditEvent(
                    event_type=BrowserAuditEventType.PROMPT_INJECTION_DETECTED,
                    session_id=session_id,
                    tab_id=target_tab_id,
                    url=sanitized_obs.url,
                    details={"warning": sanitized_obs.prompt_injection_warning},
                )
            )

        return sanitized_obs

    async def click(
        self,
        session_id: str,
        locator: BrowserElementLocator,
        tab_id: str | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> BrowserClickResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        self.policy_service.validate_action(
            action_type=BrowserActionType.CLICK,
            owner_id=owner_id,
            agent_id=agent_id,
        )

        req = BrowserClickRequest(locator=locator, tab_id=target_tab_id)
        res = await self.backend.click(session_id, target_tab_id, req)

        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.CLICKED,
                session_id=session_id,
                tab_id=target_tab_id,
                url=res.resulting_url,
                verification_status=res.verification_status,
                owner_id=owner_id,
                agent_id=agent_id,
            )
        )
        return res

    async def type_text(
        self,
        session_id: str,
        locator: BrowserElementLocator,
        text: str,
        clear_first: bool = True,
        tab_id: str | None = None,
        is_sensitive: bool = False,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> BrowserTypeResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        self.policy_service.validate_action(
            action_type=BrowserActionType.TYPE,
            owner_id=owner_id,
            agent_id=agent_id,
        )

        sensitive_check = is_sensitive or self.policy_service.is_sensitive_field(locator.to_selector())
        req = BrowserTypeRequest(
            locator=locator, text=text, clear_first=clear_first, is_sensitive=sensitive_check
        )
        res = await self.backend.type_text(session_id, target_tab_id, req)

        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.TYPED,
                session_id=session_id,
                tab_id=target_tab_id,
                owner_id=owner_id,
                agent_id=agent_id,
                details={"masked_value": res.masked_value},
            )
        )
        return res

    async def select_option(
        self,
        session_id: str,
        locator: BrowserElementLocator,
        value: str,
        tab_id: str | None = None,
    ) -> BrowserSelectResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        req = BrowserSelectRequest(locator=locator, value=value)
        return await self.backend.select_option(session_id, target_tab_id, req)

    async def scroll(
        self,
        session_id: str,
        direction: str = "down",
        amount_pixels: int = 500,
        tab_id: str | None = None,
    ) -> BrowserScrollResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        req = BrowserScrollRequest(direction=direction, amount_pixels=amount_pixels)
        return await self.backend.scroll(session_id, target_tab_id, req)

    async def wait_for_condition(
        self,
        session_id: str,
        condition: str = "load",
        locator: BrowserElementLocator | None = None,
        expected_url: str | None = None,
        timeout: float = 10.0,
        tab_id: str | None = None,
    ) -> BrowserWaitResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        req = BrowserWaitRequest(
            condition=condition, locator=locator, expected_url=expected_url, timeout=timeout
        )
        return await self.backend.wait_for_condition(session_id, target_tab_id, req)

    async def take_screenshot(
        self,
        session_id: str,
        full_page: bool = False,
        tab_id: str | None = None,
    ) -> BrowserScreenshotResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        req = BrowserScreenshotRequest(
            full_page=full_page, quality=self.settings.screenshot_quality
        )
        res = await self.backend.take_screenshot(session_id, target_tab_id, req)
        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.SCREENSHOT_TAKEN,
                session_id=session_id,
                tab_id=target_tab_id,
            )
        )
        return res

    async def extract_content(
        self,
        session_id: str,
        target: str = "text",
        tab_id: str | None = None,
    ) -> BrowserExtractResult:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)
        req = BrowserExtractRequest(target=target)
        return await self.backend.extract_content(session_id, target_tab_id, req)

    async def download_file(
        self,
        session_id: str,
        url: str,
        target_path: str,
        tab_id: str | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> BrowserDownload:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        self.policy_service.validate_action(
            action_type=BrowserActionType.DOWNLOAD,
            target_url=url,
            owner_id=owner_id,
            agent_id=agent_id,
        )

        res = await self.backend.download_file(session_id, target_tab_id, url, target_path)
        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.DOWNLOADED,
                session_id=session_id,
                tab_id=target_tab_id,
                url=url,
                details={"file_path": target_path, "file_size": res.file_size_bytes},
            )
        )
        return res

    async def upload_file(
        self,
        session_id: str,
        locator: BrowserElementLocator,
        file_path: str,
        tab_id: str | None = None,
        owner_id: str = "system",
        agent_id: str | None = None,
    ) -> BrowserUpload:
        self._get_session(session_id)
        target_tab_id = tab_id or self._get_active_tab_id(session_id)

        self.policy_service.validate_action(
            action_type=BrowserActionType.UPLOAD,
            owner_id=owner_id,
            agent_id=agent_id,
        )

        res = await self.backend.upload_file(session_id, target_tab_id, locator, file_path)
        self.audit_repo.record(
            BrowserAuditEvent(
                event_type=BrowserAuditEventType.UPLOADED,
                session_id=session_id,
                tab_id=target_tab_id,
                details={"file_path": file_path, "file_size": res.file_size_bytes},
            )
        )
        return res

    def get_audit_events(
        self, session_id: str | None = None, limit: int = 100
    ) -> list[BrowserAuditEvent]:
        return self.audit_repo.list_events(session_id=session_id, limit=limit)

    def _get_session(self, session_id: str) -> BrowserSession:
        sess = self.session_repo.get(session_id)
        if not sess or not sess.is_active:
            raise BrowserSessionNotFoundError(f"Active browser session '{session_id}' not found.")
        return sess

    def _get_active_tab_id(self, session_id: str) -> str:
        active_tab = self.tab_repo.get_active_tab(session_id)
        if not active_tab:
            tabs = self.tab_repo.list_tabs(session_id, active_only=True)
            if not tabs:
                raise BrowserTabNotFoundError(f"No open tabs found in session '{session_id}'.")
            return tabs[0].tab_id
        return active_tab.tab_id
