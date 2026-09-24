"""Domain exceptions for Module 20 — Browser Agent."""


class BrowserError(Exception):
    """Base exception for all Browser Agent errors."""


class BrowserSubsystemDisabledError(BrowserError):
    """Raised when the Browser Agent subsystem is disabled in configuration."""


class BrowserNotFoundError(BrowserError):
    """Raised when a requested browser engine or binary is not installed or available."""


class BrowserLaunchError(BrowserError):
    """Raised when launching a browser instance fails."""


class BrowserSessionNotFoundError(BrowserError):
    """Raised when a specified browser session ID does not exist."""


class BrowserTabNotFoundError(BrowserError):
    """Raised when a specified browser tab ID does not exist."""


class BrowserNavigationError(BrowserError):
    """Raised when web page navigation fails."""


class BrowserNavigationBlockedError(BrowserError):
    """Raised when navigation is blocked by URL scheme or policy."""


class BrowserDomainBlockedError(BrowserError):
    """Raised when navigation targets an unauthorized or explicitly blocked domain."""


class BrowserElementNotFoundError(BrowserError):
    """Raised when a target DOM element cannot be located on the page."""


class BrowserElementNotInteractableError(BrowserError):
    """Raised when an element is hidden, disabled, or not interactable."""


class BrowserTimeoutError(BrowserError):
    """Raised when a browser operation or condition wait times out."""


class BrowserDownloadError(BrowserError):
    """Raised when file download fails or violates security policy."""


class BrowserUploadError(BrowserError):
    """Raised when file upload fails or violates security policy."""


class BrowserPermissionDeniedError(BrowserError):
    """Raised when Module 15 PermissionGate denies a browser action."""


class BrowserApprovalRequiredError(BrowserError):
    """Raised when an action requires explicit human approval via Module 15."""


class BrowserPolicyViolationError(BrowserError):
    """Raised when a browser action violates BrowserPolicy boundaries."""


class BrowserPromptInjectionDetectedError(BrowserError):
    """Raised when web page content attempts prompt injection or policy manipulation."""


class BrowserAuthenticationBoundaryError(BrowserError):
    """Raised when an action attempts unauthorized access to user credentials or session tokens."""


class BrowserVerificationFailedError(BrowserError):
    """Raised when post-action state verification fails."""
