"""Domain exceptions for Module 19 — Application Control."""


class ApplicationControlError(Exception):
    """Base exception for all Application Control errors."""


class ApplicationSubsystemDisabledError(ApplicationControlError):
    """Raised when the Application Control subsystem is disabled in configuration."""


class ApplicationNotFoundError(ApplicationControlError):
    """Raised when no application matching the query can be found."""


class ApplicationAmbiguousError(ApplicationControlError):
    """Raised when multiple applications match a query and one cannot be selected without ambiguity."""


class ApplicationNotInstalledError(ApplicationControlError):
    """Raised when the requested application is not installed on this system."""


class ApplicationLaunchError(ApplicationControlError):
    """Raised when an application launch attempt fails at the OS level."""


class ApplicationStartupTimeoutError(ApplicationControlError):
    """Raised when an application does not become ready within the configured timeout."""


class ApplicationCloseTimeoutError(ApplicationControlError):
    """Raised when graceful close does not complete within the configured timeout."""


class ApplicationAlreadyRunningError(ApplicationControlError):
    """Raised when a launch is attempted for an application that is already running (when not allowed)."""


class ApplicationNotRunningError(ApplicationControlError):
    """Raised when an operation requires a running instance but none exists."""


class ApplicationNotRespondingError(ApplicationControlError):
    """Raised when an application is detected as not responding to input."""


class ApplicationPermissionError(ApplicationControlError):
    """Raised when Module 15 PermissionGate denies an application action."""


class ApplicationSecurityBlockedError(ApplicationControlError):
    """Raised when Module 15 emergency block or lockdown prevents the action."""


class ApplicationBackendUnavailableError(ApplicationControlError):
    """Raised when the application control backend is not available on this platform."""


class ApplicationInstanceNotFoundError(ApplicationControlError):
    """Raised when a specific application instance cannot be found."""


class ApplicationWindowNotFoundError(ApplicationControlError):
    """Raised when a window associated with an application cannot be found."""


class ApplicationArgumentError(ApplicationControlError):
    """Raised when supplied arguments fail validation."""


class ApplicationPathError(ApplicationControlError):
    """Raised when the executable path is invalid, not found, or outside allowed roots."""


class ApplicationOwnershipError(ApplicationControlError):
    """Raised when the security context does not authorize ownership of the target application."""


class ApplicationProtectedError(ApplicationControlError):
    """Raised when an action targets a protected application that cannot be forcibly controlled."""


class ApplicationRateLimitedError(ApplicationControlError):
    """Raised when an agent has exceeded the configured action rate limit."""


class ApplicationPolicyBlockedError(ApplicationControlError):
    """Raised when the ApplicationPolicyService blocks the action (second-line defence)."""


class ApplicationBlockedError(ApplicationPolicyBlockedError):
    """Raised when an application is blocked by executable name or path policy."""


class ApplicationElevationDeniedError(ApplicationControlError):
    """Raised when elevation is denied for an application action."""


class ApplicationInstanceLimitExceededError(ApplicationControlError):
    """Raised when active instance count exceeds policy limits."""


class ApplicationPolicyViolationError(ApplicationControlError):
    """Raised when an application operation violates policy rules."""


class ApplicationProcessNotFoundError(ApplicationControlError):
    """Raised when target OS process for an application instance cannot be found."""

