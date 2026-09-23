"""Unit tests for MADHAV configuration and environment management system."""

import json
from pathlib import Path

import pytest

from madhav.config.enums import Environment, LogLevel
from madhav.config.errors import ConfigurationValidationError
from madhav.config.loader import load_settings


def test_default_settings_loading() -> None:
    """Test loading default configuration values."""
    settings = load_settings()
    assert settings.application.name == "MADHAV"
    assert settings.application.service_name == "madhav"
    assert settings.server.host == "127.0.0.1"
    assert settings.server.port == 8000
    assert settings.api.prefix == "/api"
    assert settings.logging.level in (LogLevel.INFO, LogLevel.DEBUG, "INFO", "DEBUG")


def test_environment_variable_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test overriding configuration via MADHAV_ environment variables."""
    monkeypatch.setenv("MADHAV_ENVIRONMENT", "production")
    monkeypatch.setenv("MADHAV_SERVER_PORT", "9090")
    monkeypatch.setenv("MADHAV_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("MADHAV_SECRET_KEY", "custom-production-secret-key-32-chars-long!")

    settings = load_settings()
    assert settings.application.environment == Environment.PRODUCTION
    assert settings.server.port == 9090
    assert settings.logging.level == LogLevel.WARNING
    assert (
        settings.security.secret_key.get_secret_value()
        == "custom-production-secret-key-32-chars-long!"
    )


def test_invalid_port_validation() -> None:
    """Test validation failure for out-of-range port numbers."""
    with pytest.raises(ConfigurationValidationError) as exc_info:
        load_settings(env_overrides={"server": {"port": 70000}})
    assert "Invalid server port number" in str(exc_info.value)

    with pytest.raises(ConfigurationValidationError) as exc_info:
        load_settings(env_overrides={"server": {"port": -5}})
    assert "Invalid server port number" in str(exc_info.value)


def test_production_debug_mode_rejection() -> None:
    """Test production environment rejects debug=True."""
    with pytest.raises(ConfigurationValidationError) as exc_info:
        load_settings(
            env_overrides={
                "application": {"environment": Environment.PRODUCTION, "debug": True},
                "security": {"secret_key": "custom-production-secret-key-32-chars-long!"},
            }
        )
    assert "Production environment must not run with debug=True" in str(exc_info.value)


def test_production_placeholder_secret_key_rejection() -> None:
    """Test production environment rejects default placeholder secret key."""
    with pytest.raises(ConfigurationValidationError) as exc_info:
        load_settings(
            env_overrides={
                "application": {"environment": Environment.PRODUCTION, "debug": False},
                "security": {"secret_key": "development-placeholder-secret-key-32-bytes"},
            }
        )
    assert "Production environment must override default placeholder secret_key" in str(
        exc_info.value
    )


def test_production_cors_wildcard_rejection() -> None:
    """Test production environment rejects CORS wildcard origin when credentials allowed."""
    with pytest.raises(ConfigurationValidationError) as exc_info:
        load_settings(
            env_overrides={
                "application": {"environment": Environment.PRODUCTION, "debug": False},
                "security": {"secret_key": "custom-production-secret-key-32-chars-long!"},
                "cors": {"enabled": True, "allow_credentials": True, "allowed_origins": ["*"]},
            }
        )
    assert "Production CORS configuration cannot use wildcard '*' origins" in str(exc_info.value)


def test_secret_redaction() -> None:
    """Test safe_dict() / redacted() masks secret values."""
    settings = load_settings(
        env_overrides={"security": {"secret_key": "super-secret-production-key-123456789"}}
    )
    redacted = settings.redacted()
    assert redacted["security"]["secret_key"] == "***REDACTED***"
    assert "super-secret-production-key-123456789" not in json.dumps(redacted)


def test_feature_flags() -> None:
    """Test feature flag toggling."""
    settings = load_settings(
        env_overrides={
            "features": {
                "api_docs": False,
                "debug_endpoints": True,
                "experimental_features": True,
            }
        }
    )
    assert settings.features.api_docs is False
    assert settings.features.debug_endpoints is True
    assert settings.features.experimental_features is True


def test_dot_env_file_loading(tmp_path: Path) -> None:
    """Test loading configuration from custom .env file."""
    env_file = tmp_path / ".env.test"
    env_file.write_text(
        "MADHAV_SERVER_HOST=10.0.0.1\nMADHAV_SERVER_PORT=8888\nMADHAV_LOG_LEVEL=DEBUG\n"
    )

    settings = load_settings(env_file=env_file)
    assert settings.server.host == "10.0.0.1"
    assert settings.server.port == 8888
    assert settings.logging.level == LogLevel.DEBUG
