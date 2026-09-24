"""Domain exceptions for Module 21 — Web Intelligence."""


class WebIntelligenceError(Exception):
    """Base exception for all Web Intelligence errors."""

    def __init__(self, message: str, code: str = "WEB_INTEL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class ResearchNotFoundError(WebIntelligenceError):
    """Raised when a requested research task is not found."""

    def __init__(self, research_id: str) -> None:
        super().__init__(
            f"Research task with ID '{research_id}' was not found.",
            code="RESEARCH_NOT_FOUND",
        )


class SourceNotFoundError(WebIntelligenceError):
    """Raised when a requested web source is not found."""

    def __init__(self, source_id: str) -> None:
        super().__init__(
            f"Web source with ID '{source_id}' was not found.",
            code="SOURCE_NOT_FOUND",
        )


class SearchProviderError(WebIntelligenceError):
    """Raised when search provider encounters a failure."""

    def __init__(self, provider_name: str, reason: str) -> None:
        super().__init__(
            f"Search provider '{provider_name}' failed: {reason}",
            code="SEARCH_PROVIDER_ERROR",
        )


class SearchProviderUnavailableError(SearchProviderError):
    """Raised when configured search provider is offline or unreachable."""

    def __init__(self, provider_name: str) -> None:
        super().__init__(
            provider_name,
            reason="Provider is unavailable or disabled.",
        )


class SourceAcquisitionError(WebIntelligenceError):
    """Raised when acquiring content from a URL fails."""

    def __init__(self, url: str, reason: str) -> None:
        super().__init__(
            f"Failed to acquire content from URL '{url}': {reason}",
            code="SOURCE_ACQUISITION_ERROR",
        )


class InvalidResearchRequestError(WebIntelligenceError):
    """Raised when a research request is malformed or invalid."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            f"Invalid research request: {reason}",
            code="INVALID_RESEARCH_REQUEST",
        )


class ResearchBudgetExceededError(WebIntelligenceError):
    """Raised when research operation exceeds configured limits."""

    def __init__(self, limit_name: str, limit_value: int | float) -> None:
        super().__init__(
            f"Research budget limit '{limit_name}' ({limit_value}) was exceeded.",
            code="RESEARCH_BUDGET_EXCEEDED",
        )


class ResearchCancelledError(WebIntelligenceError):
    """Raised when a research request is cancelled by user or system."""

    def __init__(self, research_id: str) -> None:
        super().__init__(
            f"Research task '{research_id}' was cancelled.",
            code="RESEARCH_CANCELLED",
        )


class ResearchTimeoutError(WebIntelligenceError):
    """Raised when research operation times out."""

    def __init__(self, research_id: str, timeout_seconds: float) -> None:
        super().__init__(
            f"Research task '{research_id}' timed out after {timeout_seconds} seconds.",
            code="RESEARCH_TIMEOUT",
        )


class PromptInjectionDetectedError(WebIntelligenceError):
    """Raised when untrusted web content attempts malicious instruction injection."""

    def __init__(self, details: str) -> None:
        super().__init__(
            f"Prompt injection signal detected in web content: {details}",
            code="PROMPT_INJECTION_DETECTED",
        )


class CitationValidationError(WebIntelligenceError):
    """Raised when a citation fails validation against retrieved sources."""

    def __init__(self, citation_id: str, reason: str) -> None:
        super().__init__(
            f"Citation '{citation_id}' validation failed: {reason}",
            code="CITATION_VALIDATION_ERROR",
        )


class DomainBlockedError(WebIntelligenceError):
    """Raised when target domain is restricted by policy."""

    def __init__(self, domain: str) -> None:
        super().__init__(
            f"Domain '{domain}' is blocked by security policy.",
            code="DOMAIN_BLOCKED",
        )
