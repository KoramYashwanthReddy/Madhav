"""Configuration section models for MADHAV platform."""

from pydantic import AliasChoices, BaseModel, Field, SecretStr

from madhav.config.enums import Environment, LogLevel

_DEFAULT_SECRET_KEY_PLACEHOLDER = "development-placeholder-secret-key-32-bytes"


class ApplicationSettings(BaseModel):
    """Application identity and environment settings."""

    name: str = Field(
        default="MADHAV",
        validation_alias=AliasChoices("MADHAV_APP_NAME", "MADHAV_APPLICATION__NAME", "name"),
        description="Application name",
    )
    service_name: str = Field(
        default="madhav",
        validation_alias=AliasChoices(
            "MADHAV_SERVICE_NAME", "MADHAV_APPLICATION__SERVICE_NAME", "service_name"
        ),
        description="Service identifier",
    )
    version: str = Field(
        default="0.1.0",
        validation_alias=AliasChoices("MADHAV_VERSION", "MADHAV_APPLICATION__VERSION", "version"),
        description="Application version",
    )
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        validation_alias=AliasChoices(
            "MADHAV_ENVIRONMENT", "MADHAV_APPLICATION__ENVIRONMENT", "environment"
        ),
        description="Execution environment",
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("MADHAV_DEBUG", "MADHAV_APPLICATION__DEBUG", "debug"),
        description="Debug mode flag (must be False in production)",
    )


class ServerSettings(BaseModel):
    """HTTP server and networking configuration settings."""

    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("MADHAV_SERVER_HOST", "MADHAV_SERVER__HOST", "host"),
        description="Server bind host address",
    )
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("MADHAV_SERVER_PORT", "MADHAV_SERVER__PORT", "port"),
        description="Server listen port (1-65535)",
    )
    reload: bool = Field(
        default=True,
        validation_alias=AliasChoices("MADHAV_SERVER_RELOAD", "MADHAV_SERVER__RELOAD", "reload"),
        description="Enable auto-reload for local development",
    )
    workers: int = Field(
        default=1,
        validation_alias=AliasChoices("MADHAV_SERVER_WORKERS", "MADHAV_SERVER__WORKERS", "workers"),
        description="Number of worker processes",
    )


class APISettings(BaseModel):
    """API routing and documentation settings."""

    prefix: str = Field(
        default="/api",
        validation_alias=AliasChoices("MADHAV_API_PREFIX", "MADHAV_API__PREFIX", "prefix"),
        description="Base API route prefix",
    )
    version: str = Field(
        default="v1",
        validation_alias=AliasChoices("MADHAV_API_VERSION", "MADHAV_API__VERSION", "version"),
        description="Default API version segment",
    )
    docs_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_API_DOCS_ENABLED", "MADHAV_API__DOCS_ENABLED", "docs_enabled"
        ),
        description="Enable interactive OpenAPI UI documentation (/docs)",
    )
    openapi_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_API_OPENAPI_ENABLED", "MADHAV_API__OPENAPI_ENABLED", "openapi_enabled"
        ),
        description="Enable OpenAPI JSON schema endpoint (/openapi.json)",
    )
    redoc_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_API_REDOC_ENABLED", "MADHAV_API__REDOC_ENABLED", "redoc_enabled"
        ),
        description="Enable ReDoc interactive documentation (/redoc)",
    )


class LoggingSettings(BaseModel):
    """Structured logging configuration settings."""

    level: LogLevel = Field(
        default=LogLevel.INFO,
        validation_alias=AliasChoices("MADHAV_LOG_LEVEL", "MADHAV_LOGGING__LEVEL", "level"),
        description="Minimum active log level",
    )
    structured_logging_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_LOGGING__STRUCTURED_LOGGING_ENABLED", "structured_logging_enabled"
        ),
        description="Format logs as structured JSON",
    )
    console_logging_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_LOGGING__CONSOLE_LOGGING_ENABLED", "console_logging_enabled"
        ),
        description="Output log entries to stdout",
    )
    include_request_id: bool = Field(
        default=True,
        validation_alias=AliasChoices("MADHAV_LOGGING__INCLUDE_REQUEST_ID", "include_request_id"),
        description="Include X-Request-ID in log records",
    )


class SecuritySettings(BaseModel):
    """Foundation security boundary settings."""

    secret_key: SecretStr = Field(
        default=SecretStr(_DEFAULT_SECRET_KEY_PLACEHOLDER),
        validation_alias=AliasChoices(
            "MADHAV_SECRET_KEY", "MADHAV_SECURITY__SECRET_KEY", "secret_key"
        ),
        description="Application secret key (must be overridden in production)",
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("MADHAV_SECURITY__ALLOWED_HOSTS", "allowed_hosts"),
        description="Allowed HTTP Host header values",
    )
    trusted_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8000", "http://127.0.0.1:8000"],
        validation_alias=AliasChoices("MADHAV_SECURITY__TRUSTED_ORIGINS", "trusted_origins"),
        description="Trusted origin URLs",
    )
    secure_cookies: bool = Field(
        default=False,
        validation_alias=AliasChoices("MADHAV_SECURITY__SECURE_COOKIES", "secure_cookies"),
        description="Require Secure attribute on cookies",
    )
    require_https: bool = Field(
        default=False,
        validation_alias=AliasChoices("MADHAV_SECURITY__REQUIRE_HTTPS", "require_https"),
        description="Enforce HTTPS redirect",
    )
    security_headers_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "MADHAV_SECURITY__SECURITY_HEADERS_ENABLED", "security_headers_enabled"
        ),
        description="Enable standard security response headers",
    )


class CORSSettings(BaseModel):
    """Cross-Origin Resource Sharing (CORS) settings."""

    enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("MADHAV_CORS__ENABLED", "enabled"),
        description="Enable CORS middleware",
    )
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
        ],
        validation_alias=AliasChoices("MADHAV_CORS__ALLOWED_ORIGINS", "allowed_origins"),
        description="Allowed CORS origin URLs",
    )
    allowed_methods: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("MADHAV_CORS__ALLOWED_METHODS", "allowed_methods"),
        description="Allowed CORS HTTP methods",
    )
    allowed_headers: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias=AliasChoices("MADHAV_CORS__ALLOWED_HEADERS", "allowed_headers"),
        description="Allowed CORS HTTP headers",
    )
    allow_credentials: bool = Field(
        default=True,
        validation_alias=AliasChoices("MADHAV_CORS__ALLOW_CREDENTIALS", "allow_credentials"),
        description="Allow credentials in CORS requests",
    )


class FeatureFlags(BaseModel):
    """Platform feature flags foundation."""

    api_docs: bool = Field(
        default=True,
        validation_alias=AliasChoices("MADHAV_FEATURES__API_DOCS", "api_docs"),
        description="Feature flag for API documentation",
    )
    debug_endpoints: bool = Field(
        default=False,
        validation_alias=AliasChoices("MADHAV_FEATURES__DEBUG_ENDPOINTS", "debug_endpoints"),
        description="Feature flag for debug diagnostics endpoints",
    )
    experimental_features: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "MADHAV_FEATURES__EXPERIMENTAL_FEATURES", "experimental_features"
        ),
        description="Feature flag for experimental functionality",
    )
