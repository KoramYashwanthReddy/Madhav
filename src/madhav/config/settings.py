"""Root configuration model powered by Pydantic Settings."""

from functools import lru_cache
from typing import Any

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from madhav.config.sections import (
    AIRuntimeSettings,
    APISettings,
    ApplicationSettings,
    ContextManagementSettings,
    CORSSettings,
    FeatureFlags,
    IdentitySettings,
    LoggingSettings,
    ModelManagementSettings,
    SecuritySettings,
    ServerSettings,
)
from madhav.config.validators import (
    validate_context_settings,
    validate_logging_settings,
    validate_production_settings,
    validate_server_settings,
)


class Settings(BaseSettings):
    """MADHAV Root Configuration Model.

    Combines application, server, API, logging, security, CORS, identity, AI runtime,
    model management, context management, and feature flag settings.
    Supports environment variables prefixed with `MADHAV_` and double-underscore nested keys.
    """

    model_config = SettingsConfigDict(
        env_prefix="MADHAV_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    identity: IdentitySettings = Field(default_factory=IdentitySettings)
    ai_runtime: AIRuntimeSettings = Field(default_factory=AIRuntimeSettings)
    models: ModelManagementSettings = Field(default_factory=ModelManagementSettings)
    context: ContextManagementSettings = Field(default_factory=ContextManagementSettings)

    def model_post_init(self, __context: Any) -> None:
        """Validate settings after initialization."""
        self.validate_configuration()

    def validate_configuration(self) -> None:
        """Run validation routines across all configuration categories."""
        validate_server_settings(self.server)
        validate_logging_settings(self.logging)
        validate_production_settings(self.application, self.security, self.cors)
        validate_context_settings(self.context)


    def safe_dict(self) -> dict[str, Any]:
        """Return a dictionary representation with sensitive secrets redacted."""
        raw_dict = self.model_dump()
        return _redact_dict(raw_dict)

    def redacted(self) -> dict[str, Any]:
        """Alias for safe_dict() returning redacted configuration."""
        return self.safe_dict()


def _redact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask secret values and SecretStr instances in dictionary."""
    redacted_result: dict[str, Any] = {}
    secret_key_names = {"secret_key", "password", "token", "api_key", "credentials"}

    for key, val in d.items():
        if isinstance(val, SecretStr):
            redacted_result[key] = "***REDACTED***"
        elif isinstance(val, dict):
            redacted_result[key] = _redact_dict(val)
        elif key.lower() in secret_key_names:
            redacted_result[key] = "***REDACTED***"
        else:
            redacted_result[key] = val

    return redacted_result


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retrieve cached global application settings instance."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings instance (primarily for test isolation)."""
    get_settings.cache_clear()
