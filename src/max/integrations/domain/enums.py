"""Domain enums for Module 29 — External Integrations."""

from enum import StrEnum


class ConnectionStatus(StrEnum):
    """Lifecycle state of an external service connection."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"


class AuthenticationType(StrEnum):
    """Supported external authentication mechanisms."""

    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    BASIC_AUTH = "BASIC_AUTH"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    CUSTOM = "CUSTOM"
    NONE = "NONE"


class IntegrationCategory(StrEnum):
    """Extensible categories of external service integrations."""

    EMAIL = "EMAIL"
    CALENDAR = "CALENDAR"
    STORAGE = "STORAGE"
    COMMUNICATION = "COMMUNICATION"
    DEVELOPER = "DEVELOPER"
    PRODUCTIVITY = "PRODUCTIVITY"
    FINANCE = "FINANCE"
    SOCIAL = "SOCIAL"
    AI = "AI"
    ANALYTICS = "ANALYTICS"
    DATABASE = "DATABASE"
    CRM = "CRM"
    DOCUMENTS = "DOCUMENTS"
    IDENTITY = "IDENTITY"
    OTHER = "OTHER"


class RiskLevel(StrEnum):
    """Structured security risk classification for external integration actions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class WebhookProcessingStatus(StrEnum):
    """Processing stage status for incoming webhook events."""

    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    EMITTED = "EMITTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ErrorCode(StrEnum):
    """Normalized provider-neutral error categories."""

    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN = "UNKNOWN"


class IntegrationStatus(StrEnum):
    """Status of an integration definition."""

    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    DISABLED = "DISABLED"
