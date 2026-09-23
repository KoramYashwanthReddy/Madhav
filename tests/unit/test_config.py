"""Unit tests for MADHAV configuration and environment system."""

import pytest

from madhav.common.types import LogLevel
from madhav.config.enums import Environment
from madhav.config.errors import ConfigurationError
from madhav.config.sections import (
    ApplicationSettings,
    CORSSettings,
    FeatureFlags,
    LoggingSettings,
    ServerSettings,
)
from madhav.config.settings import Settings, clear_settings_cache, get_settings


def test_default_settings() -> None:
    """Verify built-in default configuration values."""
    settings = Settings(application=ApplicationSettings(environment=Environment.DEVELOPMENT))
    assert settings.application.name == "MADHAV"
    assert settings.application.service == "madhav"
    assert settings.application.version == "0.1.0"
    assert settings.application.environment == Environment.DEVELOPMENT
    assert settings.application.debug is False

    assert settings.server.host == "127.0.0.1"
    assert settings.server.port == 8000
    assert settings.server.reload is False

    assert settings.api.prefix == "/api"
    assert settings.api.version == "v1"

    assert settings.logging.level == LogLevel.INFO
    assert settings.logging.json_format is True

    assert settings.cors.enabled is True
    assert settings.features.api_docs is True


def test_env_var_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify environment variables override default settings."""
    monkeypatch.setenv("MADHAV_SERVER__PORT", "9090")
    monkeypatch.setenv("MADHAV_LOGGING__LEVEL", "DEBUG")
    monkeypatch.setenv("MADHAV_APPLICATION__DEBUG", "true")

    clear_settings_cache()
    settings = get_settings()

    assert settings.server.port == 9090
    assert settings.logging.level == LogLevel.DEBUG
    assert settings.application.debug is True


def test_invalid_port_validation() -> None:
    """Verify invalid server port raises ConfigurationError."""
    with pytest.raises(ConfigurationError) as exc_info:
        Settings(server=ServerSettings(port=70000))
    assert "Invalid server port: 70000" in str(exc_info.value)

    with pytest.raises(ConfigurationError):
        Settings(server=ServerSettings(port=0))


def test_invalid_log_level() -> None:
    """Verify invalid log level raises validation error."""
    with pytest.raises(Exception) as exc_info:
        Settings(logging=LoggingSettings(level="INVALID_LEVEL"))  # type: ignore[arg-type]
    assert "INVALID_LEVEL" in str(exc_info.value)


def test_production_debug_violation() -> None:
    """Verify production environment rejects debug=True."""
    with pytest.raises(ConfigurationError) as exc_info:
        Settings(application=ApplicationSettings(environment=Environment.PRODUCTION, debug=True))
    assert "debug mode cannot be enabled in production" in str(exc_info.value)


def test_production_cors_wildcard_violation() -> None:
    """Verify production environment rejects wildcard CORS origin with credentials."""
    with pytest.raises(ConfigurationError) as exc_info:
        Settings(
            application=ApplicationSettings(environment=Environment.PRODUCTION),
            cors=CORSSettings(enabled=True, allow_credentials=True, allowed_origins=["*"]),
        )
    assert "wildcard origin '*' is forbidden" in str(exc_info.value)


def test_secret_redaction() -> None:
    """Verify safe_dict() and redacted() mask sensitive fields."""
    settings = Settings()
    safe_data = settings.safe_dict()

    assert safe_data["security"]["secret_key"] == "***REDACTED***"
    assert safe_data["application"]["name"] == "MADHAV"
    assert safe_data["server"]["port"] == 8000

    redacted_data = settings.redacted()
    assert redacted_data["security"]["secret_key"] == "***REDACTED***"


def test_feature_flags() -> None:
    """Verify feature flag toggles."""
    flags = FeatureFlags(api_docs=True, debug_endpoints=False)
    assert flags.api_docs is True
    assert flags.debug_endpoints is False
