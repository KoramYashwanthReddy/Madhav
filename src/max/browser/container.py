"""Global dependency injection container for Module 20 — Browser Agent."""

from max.browser.backends.base import BrowserBackend
from max.browser.backends.mock import MockBrowserBackend
from max.browser.backends.playwright import PlaywrightBrowserBackend
from max.browser.repositories.repositories import (
    BrowserAuditRepository,
    BrowserSessionRepository,
    BrowserTabRepository,
)
from max.browser.security.browser_policy import BrowserPolicyService
from max.browser.services.browser_service import BrowserService
from max.config.settings import get_settings
from max.security.container import get_security_container
from max.security.services.gate import PermissionGate


class BrowserContainer:
    """Dependency injection container for the Browser Agent subsystem."""

    def __init__(
        self,
        use_mock_backend: bool | None = None,
        custom_backend: BrowserBackend | None = None,
    ) -> None:
        cfg = get_settings().browser
        self.settings = cfg

        # Repositories
        self.session_repo = BrowserSessionRepository()
        self.tab_repo = BrowserTabRepository()
        self.audit_repo = BrowserAuditRepository()

        # Module 15 Permission Gate integration
        self.permission_gate: PermissionGate | None = None
        try:
            sec_container = get_security_container()
            self.permission_gate = sec_container.gate
        except Exception:
            self.permission_gate = None

        # Security policy service
        self.policy_service = BrowserPolicyService(
            settings=cfg,
            permission_gate=self.permission_gate,
        )

        # Backend selection:
        # - use_mock_backend=True  → always mock
        # - use_mock_backend=None  → mock if headless=False (no display) or Playwright unavailable
        # - use_mock_backend=False → always Playwright
        if custom_backend is not None:
            self.backend: BrowserBackend = custom_backend
        elif use_mock_backend is True:
            self.backend = MockBrowserBackend()
        elif use_mock_backend is False:
            self.backend = PlaywrightBrowserBackend(headless=cfg.headless)
        else:
            # Auto-detect: prefer Playwright if available, fall back to mock
            try:
                import playwright  # noqa: F401
                self.backend = PlaywrightBrowserBackend(headless=cfg.headless)
            except ImportError:
                self.backend = MockBrowserBackend()

        # Primary service facade
        self.browser_service = BrowserService(
            backend=self.backend,
            settings=cfg,
            session_repo=self.session_repo,
            tab_repo=self.tab_repo,
            audit_repo=self.audit_repo,
            policy_service=self.policy_service,
        )


_container_instance: BrowserContainer | None = None


def get_browser_container(
    use_mock_backend: bool | None = None,
) -> BrowserContainer:
    """Retrieve or initialize the global BrowserContainer instance."""
    global _container_instance
    if _container_instance is None:
        _container_instance = BrowserContainer(
            use_mock_backend=use_mock_backend
        )
    return _container_instance


def reset_browser_container() -> None:
    """Reset the global BrowserContainer instance (used for test isolation)."""
    global _container_instance
    _container_instance = None
