"""Domain enumerations for Module 20 — Browser Agent."""

from enum import StrEnum


class BrowserEngine(StrEnum):
    """Engine technology for browser runtime."""

    CHROMIUM = "CHROMIUM"
    FIREFOX = "FIREFOX"
    WEBKIT = "WEBKIT"
    MOCK = "MOCK"


class BrowserType(StrEnum):
    """Classification of browser type."""

    DESKTOP = "DESKTOP"
    HEADLESS = "HEADLESS"
    CONTAINER = "CONTAINER"
    MOCK = "MOCK"


class BrowserStatus(StrEnum):
    """Lifecycle state machine for browser sessions."""

    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    NAVIGATING = "NAVIGATING"
    OBSERVING = "OBSERVING"
    EXECUTING = "EXECUTING"
    WAITING = "WAITING"
    ERROR = "ERROR"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class BrowserTabStatus(StrEnum):
    """Lifecycle state of an individual browser tab."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    NAVIGATING = "NAVIGATING"
    LOADING = "LOADING"
    CLOSED = "CLOSED"


class BrowserElementType(StrEnum):
    """Taxonomy of interactive web elements."""

    BUTTON = "BUTTON"
    INPUT = "INPUT"
    TEXTAREA = "TEXTAREA"
    SELECT = "SELECT"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"
    LINK = "LINK"
    FORM = "FORM"
    IMAGE = "IMAGE"
    HEADING = "HEADING"
    TEXT = "TEXT"
    IFRAME = "IFRAME"
    OTHER = "OTHER"


class BrowserActionType(StrEnum):
    """Supported browser operations."""

    OPEN_SESSION = "OPEN_SESSION"
    CLOSE_SESSION = "CLOSE_SESSION"
    CREATE_TAB = "CREATE_TAB"
    SWITCH_TAB = "SWITCH_TAB"
    CLOSE_TAB = "CLOSE_TAB"
    NAVIGATE = "NAVIGATE"
    BACK = "BACK"
    FORWARD = "FORWARD"
    RELOAD = "RELOAD"
    OBSERVE = "OBSERVE"
    FIND_ELEMENT = "FIND_ELEMENT"
    CLICK = "CLICK"
    TYPE = "TYPE"
    SELECT = "SELECT"
    SCROLL = "SCROLL"
    WAIT = "WAIT"
    SCREENSHOT = "SCREENSHOT"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    EXTRACT_LINKS = "EXTRACT_LINKS"
    EXTRACT_FORMS = "EXTRACT_FORMS"
    DOWNLOAD = "DOWNLOAD"
    UPLOAD = "UPLOAD"


class BrowserActionStatus(StrEnum):
    """Execution status of a browser action request."""

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    AUTHORIZED = "AUTHORIZED"
    READY = "READY"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    SUCCESS = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    SIMULATED = "SIMULATED"


class BrowserVerificationStatus(StrEnum):
    """Result of post-action verification."""

    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    ACTION_COMPLETED_UNVERIFIED = "UNVERIFIED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class BrowserRiskLevel(StrEnum):
    """Risk classification for browser operations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BrowserAuditEventType(StrEnum):
    """Audit event types recorded during browser interactions."""

    SESSION_CREATED = "SESSION_CREATED"
    SESSION_CLOSED = "SESSION_CLOSED"
    TAB_CREATED = "TAB_CREATED"
    TAB_CLOSED = "TAB_CLOSED"
    NAVIGATED = "NAVIGATED"
    CLICKED = "CLICKED"
    TYPED = "TYPED"
    SELECTED = "SELECTED"
    SCROLLED = "SCROLLED"
    SCREENSHOT_TAKEN = "SCREENSHOT_TAKEN"
    DOWNLOADED = "DOWNLOADED"
    UPLOADED = "UPLOADED"
    PROMPT_INJECTION_DETECTED = "PROMPT_INJECTION_DETECTED"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    PERMISSION_DENIED = "PERMISSION_DENIED"
