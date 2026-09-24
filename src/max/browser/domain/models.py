"""Domain models for Module 20 — Browser Agent.

All models are immutable Pydantic value objects representing browser sessions,
tabs, pages, elements, navigation, interactions, security policies, and audit logs.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from max.browser.domain.enums import (
    BrowserActionStatus,
    BrowserActionType,
    BrowserAuditEventType,
    BrowserElementType,
    BrowserEngine,
    BrowserRiskLevel,
    BrowserStatus,
    BrowserTabStatus,
    BrowserType,
    BrowserVerificationStatus,
)

# ---------------------------------------------------------------------------
# Identifiers & Value Objects
# ---------------------------------------------------------------------------


class BrowserId(BaseModel):
    """Unique browser instance identifier."""

    value: str = Field(default_factory=lambda: f"brw_{uuid.uuid4().hex[:12]}")

    def __str__(self) -> str:
        return self.value


class BrowserSessionId(BaseModel):
    """Unique browser session identifier."""

    value: str = Field(default_factory=lambda: f"bsess_{uuid.uuid4().hex[:12]}")

    def __str__(self) -> str:
        return self.value


class BrowserTabId(BaseModel):
    """Unique browser tab identifier."""

    value: str = Field(default_factory=lambda: f"btab_{uuid.uuid4().hex[:12]}")

    def __str__(self) -> str:
        return self.value


class BrowserElementId(BaseModel):
    """Unique element identifier within a page observation."""

    value: str = Field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")

    def __str__(self) -> str:
        return self.value


class BrowserUrl(BaseModel):
    """Structured, validated URL representation."""

    raw_url: str = Field(..., description="Raw URL string")
    scheme: str = Field(default="https", description="URL scheme (http, https)")
    domain: str = Field(default="", description="Hostname/domain part")
    path: str = Field(default="/", description="Path part")
    query: str = Field(default="", description="Query string")

    def __str__(self) -> str:
        return self.raw_url


# ---------------------------------------------------------------------------
# Browser Setup & Profile Models
# ---------------------------------------------------------------------------


class BrowserConfiguration(BaseModel):
    """Session-level runtime browser configuration settings."""

    engine: BrowserEngine = Field(default=BrowserEngine.CHROMIUM)
    browser_type: BrowserType = Field(default=BrowserType.HEADLESS)
    headless: bool = Field(default=True)
    user_agent: str | None = Field(default=None)
    viewport_width: int = Field(default=1280, ge=320, le=3840)
    viewport_height: int = Field(default=800, ge=240, le=2160)
    navigation_timeout: float = Field(default=30.0, ge=1.0)
    action_timeout: float = Field(default=15.0, ge=1.0)
    download_directory: str | None = Field(default=None)
    accept_downloads: bool = Field(default=True)
    extra_headers: dict[str, str] = Field(default_factory=dict)


class BrowserProfile(BaseModel):
    """Isolated, Max-controlled browser environment profile."""

    profile_id: str = Field(default_factory=lambda: f"bprof_{uuid.uuid4().hex[:12]}")
    name: str = Field(default="Max Default Profile")
    is_incognito: bool = Field(default=True)
    storage_state_path: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BrowserMetadata(BaseModel):
    """Platform and backend operational metadata."""

    engine: BrowserEngine = Field(default=BrowserEngine.CHROMIUM)
    version: str = Field(default="1.0.0")
    user_agent: str = Field(default="Max-BrowserAgent/1.0")
    is_headless: bool = Field(default=True)
    active_sessions_count: int = Field(default=0)


# ---------------------------------------------------------------------------
# Element, Page, and Observation Models
# ---------------------------------------------------------------------------


class BrowserElementLocator(BaseModel):
    """Flexible element identification criteria."""

    css: str | None = Field(default=None)
    text: str | None = Field(default=None)
    role: str | None = Field(default=None)
    label: str | None = Field(default=None)
    placeholder: str | None = Field(default=None)
    name: str | None = Field(default=None)
    test_id: str | None = Field(default=None)
    xpath: str | None = Field(default=None)

    def to_selector(self) -> str:
        """Derive primary selector string for Playwright."""
        if self.css:
            return self.css
        if self.text:
            return f"text={self.text}"
        if self.label:
            return f"label={self.label}"
        if self.placeholder:
            return f"[placeholder='{self.placeholder}']"
        if self.role:
            return f"role={self.role}"
        if self.name:
            return f"[name='{self.name}']"
        if self.test_id:
            return f"[data-testid='{self.test_id}']"
        if self.xpath:
            return self.xpath
        return "*"


class BrowserElement(BaseModel):
    """Observed DOM element snapshot."""

    element_id: str = Field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")
    element_type: BrowserElementType = Field(default=BrowserElementType.OTHER)
    tag_name: str = Field(default="div")
    text: str = Field(default="")
    value: str | None = Field(default=None)
    attributes: dict[str, str] = Field(default_factory=dict)
    visible: bool = Field(default=True)
    enabled: bool = Field(default=True)
    focused: bool = Field(default=False)
    is_sensitive: bool = Field(default=False, description="True for password, credit card, or secret inputs")
    locator: BrowserElementLocator = Field(default_factory=BrowserElementLocator)


class BrowserLink(BaseModel):
    """Extracted link on a web page."""

    text: str = Field(default="")
    url: str = Field(...)
    target: str | None = Field(default=None)
    is_external: bool = Field(default=False)


class BrowserInput(BaseModel):
    """Extracted form input field."""

    name: str = Field(default="")
    input_type: str = Field(default="text")
    value: str | None = Field(default=None)
    label: str | None = Field(default=None)
    is_required: bool = Field(default=False)
    is_sensitive: bool = Field(default=False)


class BrowserForm(BaseModel):
    """Extracted HTML form structure."""

    form_id: str = Field(default_factory=lambda: f"form_{uuid.uuid4().hex[:8]}")
    action_url: str = Field(default="")
    method: str = Field(default="GET")
    inputs: list[BrowserInput] = Field(default_factory=list)
    submit_button_text: str | None = Field(default=None)
    has_sensitive_fields: bool = Field(default=False)


class BrowserPageMetadata(BaseModel):
    """Metadata extracted from page head/header tags."""

    title: str = Field(default="")
    description: str | None = Field(default=None)
    canonical_url: str | None = Field(default=None)
    content_type: str = Field(default="text/html")
    content_length_bytes: int = Field(default=0)


class BrowserObservation(BaseModel):
    """Bounded, safe page observation structure returned to AI agent."""

    url: str = Field(...)
    title: str = Field(default="")
    page_metadata: BrowserPageMetadata = Field(default_factory=BrowserPageMetadata)
    text_content: str = Field(default="", description="Sanitized, truncated visible text")
    elements: list[BrowserElement] = Field(default_factory=list)
    links: list[BrowserLink] = Field(default_factory=list)
    forms: list[BrowserForm] = Field(default_factory=list)
    prompt_injection_warning: str | None = Field(default=None)
    is_untrusted_web_content: bool = Field(default=True, description="Always True for web content")
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BrowserPage(BaseModel):
    """Current page state in a tab."""

    url: str = Field(default="about:blank")
    title: str = Field(default="")
    status: str = Field(default="ready")
    last_observation: BrowserObservation | None = Field(default=None)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ---------------------------------------------------------------------------
# Sessions & Tabs
# ---------------------------------------------------------------------------


class BrowserTab(BaseModel):
    """Represents a single tab within a browser session."""

    tab_id: str = Field(default_factory=lambda: f"btab_{uuid.uuid4().hex[:12]}")
    session_id: str = Field(...)
    url: str = Field(default="about:blank")
    title: str = Field(default="New Tab")
    status: BrowserTabStatus = Field(default=BrowserTabStatus.ACTIVE)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))
    page: BrowserPage = Field(default_factory=BrowserPage)

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" in data and "tab_id" not in data:
                data["tab_id"] = data.pop("id")
        return data


class BrowserSession(BaseModel):
    """Represents an isolated, active browser instance/session."""

    session_id: str = Field(default_factory=lambda: f"bsess_{uuid.uuid4().hex[:12]}")
    owner_id: str = Field(default="system")
    status: BrowserStatus = Field(default=BrowserStatus.READY)
    engine: BrowserEngine = Field(default=BrowserEngine.CHROMIUM)
    browser_type: BrowserType = Field(default=BrowserType.HEADLESS)
    profile: BrowserProfile = Field(default_factory=BrowserProfile)
    configuration: BrowserConfiguration = Field(default_factory=BrowserConfiguration)
    active_tab_id: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        return self.status in (
            BrowserStatus.READY,
            BrowserStatus.NAVIGATING,
            BrowserStatus.OBSERVING,
            BrowserStatus.EXECUTING,
            BrowserStatus.WAITING,
        )


# ---------------------------------------------------------------------------
# Specific Action Requests & Results
# ---------------------------------------------------------------------------


class BrowserNavigationRequest(BaseModel):
    url: str = Field(...)
    tab_id: str | None = Field(default=None)
    timeout: float | None = Field(default=None)


class BrowserNavigationResult(BaseModel):
    url: str = Field(...)
    title: str = Field(default="")
    status_code: int = Field(default=200)
    redirect_chain: list[str] = Field(default_factory=list)
    success: bool = Field(default=True)


class BrowserClickRequest(BaseModel):
    locator: BrowserElementLocator = Field(...)
    tab_id: str | None = Field(default=None)
    button: str = Field(default="left")
    click_count: int = Field(default=1)


class BrowserClickResult(BaseModel):
    success: bool = Field(default=True)
    resulting_url: str = Field(default="")
    verification_status: BrowserVerificationStatus = Field(default=BrowserVerificationStatus.VERIFIED)


class BrowserTypeRequest(BaseModel):
    locator: BrowserElementLocator = Field(...)
    text: str = Field(...)
    clear_first: bool = Field(default=True)
    tab_id: str | None = Field(default=None)
    is_sensitive: bool = Field(default=False)


class BrowserTypeResult(BaseModel):
    success: bool = Field(default=True)
    masked_value: str = Field(default="***")


class BrowserSelectRequest(BaseModel):
    locator: BrowserElementLocator = Field(...)
    value: str = Field(...)
    tab_id: str | None = Field(default=None)


class BrowserSelectResult(BaseModel):
    success: bool = Field(default=True)
    selected_value: str = Field(default="")


class BrowserScrollRequest(BaseModel):
    direction: str = Field(default="down", description="'up', 'down', 'top', 'bottom'")
    amount_pixels: int = Field(default=500, ge=1)
    tab_id: str | None = Field(default=None)


class BrowserScrollResult(BaseModel):
    success: bool = Field(default=True)
    current_scroll_y: int = Field(default=0)


class BrowserWaitRequest(BaseModel):
    condition: str = Field(default="load", description="'load', 'element', 'url', 'timeout'")
    locator: BrowserElementLocator | None = Field(default=None)
    expected_url: str | None = Field(default=None)
    timeout: float = Field(default=10.0, ge=0.1)
    tab_id: str | None = Field(default=None)


class BrowserWaitResult(BaseModel):
    success: bool = Field(default=True)
    elapsed_seconds: float = Field(default=0.0)


class BrowserScreenshotRequest(BaseModel):
    full_page: bool = Field(default=False)
    quality: int = Field(default=80, ge=1, le=100)
    tab_id: str | None = Field(default=None)


class BrowserScreenshotResult(BaseModel):
    image_bytes: bytes = Field(default=b"")
    mime_type: str = Field(default="image/jpeg")
    file_path: str | None = Field(default=None)


class BrowserExtractRequest(BaseModel):
    target: str = Field(default="text", description="'text', 'links', 'forms'")
    tab_id: str | None = Field(default=None)


class BrowserExtractResult(BaseModel):
    text: str | None = Field(default=None)
    links: list[BrowserLink] = Field(default_factory=list)
    forms: list[BrowserForm] = Field(default_factory=list)

    @property
    def extracted_text(self) -> str:
        return self.text or ""


class BrowserDownload(BaseModel):
    download_id: str = Field(default_factory=lambda: f"dl_{uuid.uuid4().hex[:12]}")
    url: str = Field(...)
    suggested_filename: str = Field(default="download.bin")
    file_path: str = Field(...)
    file_size_bytes: int = Field(default=0)
    completed: bool = Field(default=True)


class BrowserUpload(BaseModel):
    upload_id: str = Field(default_factory=lambda: f"up_{uuid.uuid4().hex[:12]}")
    file_path: str = Field(...)
    target_locator: BrowserElementLocator = Field(...)
    file_size_bytes: int = Field(default=0)
    completed: bool = Field(default=True)


# ---------------------------------------------------------------------------
# General Action Request / Result
# ---------------------------------------------------------------------------


class BrowserActionRequest(BaseModel):
    """Generic structured request wrapper for all browser operations."""

    action_id: str = Field(default_factory=lambda: f"bact_{uuid.uuid4().hex[:12]}")
    action_type: BrowserActionType = Field(...)
    session_id: str | None = Field(default=None)
    tab_id: str | None = Field(default=None)
    url: str | None = Field(default=None)
    locator: BrowserElementLocator | None = Field(default=None)
    text: str | None = Field(default=None)
    value: str | None = Field(default=None)
    file_path: str | None = Field(default=None)
    timeout: float | None = Field(default=None)
    owner_id: str = Field(default="system")
    agent_id: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "id" in data and "action_id" not in data:
                data["action_id"] = data.pop("id")
        return data


class BrowserActionResult(BaseModel):
    """Generic result wrapper for browser operations."""

    action_id: str = Field(...)
    action_type: BrowserActionType = Field(...)
    status: BrowserActionStatus = Field(default=BrowserActionStatus.COMPLETED)
    session_id: str | None = Field(default=None)
    tab_id: str | None = Field(default=None)
    url: str | None = Field(default=None)
    observation: BrowserObservation | None = Field(default=None)
    verification_status: BrowserVerificationStatus = Field(default=BrowserVerificationStatus.VERIFIED)
    failure_message: str | None = Field(default=None)
    message: str | None = Field(default=None)
    duration: float = Field(default=0.0)
    executed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status in (BrowserActionStatus.COMPLETED, BrowserActionStatus.SUCCESS)

    @property
    def error_message(self) -> str | None:
        return self.failure_message


# ---------------------------------------------------------------------------
# Policy & Permission Models
# ---------------------------------------------------------------------------


class BrowserPermission(BaseModel):
    """Permission statement governing browser capability."""

    action: BrowserActionType = Field(...)
    allowed: bool = Field(default=True)
    requires_approval: bool = Field(default=False)
    risk_level: BrowserRiskLevel = Field(default=BrowserRiskLevel.LOW)


class BrowserPolicy(BaseModel):
    """Browser security policy bounds."""

    policy_id: str = Field(default_factory=lambda: f"bpol_{uuid.uuid4().hex[:12]}")
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    allowed_schemes: list[str] = Field(default_factory=lambda: ["http", "https"])
    blocked_schemes: list[str] = Field(
        default_factory=lambda: ["javascript", "data", "file", "about", "chrome", "edge", "devtools"]
    )
    max_redirects: int = Field(default=5)
    allow_downloads: bool = Field(default=True)
    allow_uploads: bool = Field(default=True)
    max_page_observation_bytes: int = Field(default=1048576)
    notes: str = Field(default="")


# ---------------------------------------------------------------------------
# Audit Event
# ---------------------------------------------------------------------------


class BrowserAuditEvent(BaseModel):
    """Immutable audit event for recording browser actions."""

    event_id: str = Field(default_factory=lambda: f"bevt_{uuid.uuid4().hex[:12]}")
    event_type: BrowserAuditEventType = Field(...)
    session_id: str | None = Field(default=None)
    tab_id: str | None = Field(default=None)
    action_id: str | None = Field(default=None)
    owner_id: str = Field(default="system")
    agent_id: str | None = Field(default=None)
    url: str | None = Field(default=None)
    status: BrowserActionStatus = Field(default=BrowserActionStatus.COMPLETED)
    risk_level: BrowserRiskLevel = Field(default=BrowserRiskLevel.LOW)
    verification_status: BrowserVerificationStatus = Field(default=BrowserVerificationStatus.VERIFIED)
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
