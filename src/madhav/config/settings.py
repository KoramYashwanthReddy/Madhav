"""Root Settings model using pydantic-settings for MADHAV platform."""

import os
from typing import Any

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from madhav.config.enums import Environment, LogLevel
from madhav.config.errors import ConfigurationValidationError
from madhav.config.sections import (
    _DEFAULT_SECRET_KEY_PLACEHOLDER,
    APISettings,
    ApplicationSettings,
    CORSSettings,
    FeatureFlags,
    LoggingSettings,
    SecuritySettings,
    ServerSettings,
)


class Settings(BaseSettings):
    """MADHAV platform root settings container."""

    model_config = SettingsConfigDict(
        env_prefix="MADHAV_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    application: ApplicationSettings = Field(default_factory=ApplicationSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    api: APISettings = Field(default_factory=APISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    features: FeatureFlags = Field(default_factory=FeatureFlags)

    @model_validator(mode="before")
    @classmethod
    def _map_env_vars(cls, data: Any) -> Any:
        """Pre-process raw settings dictionary to map flat env vars to nested sections."""
        if not isinstance(data, dict):
            return data

        res: dict[str, Any] = dict(data)
        lower_map: dict[str, Any] = {k.lower(): v for k, v in res.items() if isinstance(k, str)}

        app_raw = res.get("application")
        app_data: dict[str, Any] = dict(app_raw) if isinstance(app_raw, dict) else {}

        server_raw = res.get("server")
        server_data: dict[str, Any] = dict(server_raw) if isinstance(server_raw, dict) else {}

        log_raw = res.get("logging")
        log_data: dict[str, Any] = dict(log_raw) if isinstance(log_raw, dict) else {}

        sec_raw = res.get("security")
        sec_data: dict[str, Any] = dict(sec_raw) if isinstance(sec_raw, dict) else {}

        # 1. Application mappings
        env_val = (
            lower_map.get("madhav_environment")
            or lower_map.get("environment")
            or os.getenv("MADHAV_ENVIRONMENT")
        )
        if env_val is not None and "environment" not in app_data:
            app_data["environment"] = env_val

        debug_val = (
            lower_map.get("madhav_debug") or lower_map.get("debug") or os.getenv("MADHAV_DEBUG")
        )
        if debug_val is not None and "debug" not in app_data:
            app_data["debug"] = debug_val

        # 2. Server mappings
        host_val = (
            lower_map.get("madhav_server_host")
            or lower_map.get("server_host")
            or os.getenv("MADHAV_SERVER_HOST")
        )
        if host_val is not None and "host" not in server_data:
            server_data["host"] = host_val

        port_val = (
            lower_map.get("madhav_server_port")
            or lower_map.get("server_port")
            or os.getenv("MADHAV_SERVER_PORT")
        )
        if port_val is not None and "port" not in server_data:
            server_data["port"] = port_val

        # 3. Logging mappings
        level_val = (
            lower_map.get("madhav_log_level")
            or lower_map.get("log_level")
            or os.getenv("MADHAV_LOG_LEVEL")
        )
        if level_val is not None and "level" not in log_data:
            log_data["level"] = level_val

        # 4. Security mappings
        secret_val = (
            lower_map.get("madhav_secret_key")
            or lower_map.get("secret_key")
            or os.getenv("MADHAV_SECRET_KEY")
        )
        if secret_val is not None and "secret_key" not in sec_data:
            sec_data["secret_key"] = secret_val

        if app_data:
            res["application"] = app_data
        if server_data:
            res["server"] = server_data
        if log_data:
            res["logging"] = log_data
        if sec_data:
            res["security"] = sec_data

        return res

    def validate_runtime_invariants(self) -> None:
        """Validate critical configuration constraints and production security rules."""
        # 1. Port boundary check
        if not (1 <= self.server.port <= 65535):
            raise ConfigurationValidationError(
                message=(
                    f"Invalid server port number: {self.server.port}. "
                    "Port must be between 1 and 65535."
                ),
                details={"port": self.server.port},
            )

        # 2. Log level validation (handled by LogLevel enum, but double check)
        if not isinstance(self.logging.level, LogLevel):
            try:
                LogLevel(str(self.logging.level).upper())
            except ValueError as err:
                raise ConfigurationValidationError(
                    message=f"Invalid log level: {self.logging.level}",
                    details={"log_level": str(self.logging.level)},
                ) from err

        # 3. Production security invariants
        if self.application.environment == Environment.PRODUCTION:
            if self.application.debug:
                raise ConfigurationValidationError(
                    message="Production environment must not run with debug=True.",
                    details={"environment": "production", "debug": True},
                )

            if (
                self.cors.enabled
                and self.cors.allow_credentials
                and "*" in self.cors.allowed_origins
            ):
                raise ConfigurationValidationError(
                    message=(
                        "Production CORS configuration cannot use wildcard '*'"
                        " origins when allow_credentials=True."
                    ),
                    details={"allowed_origins": self.cors.allowed_origins},
                )

            if self.security.secret_key.get_secret_value() == _DEFAULT_SECRET_KEY_PLACEHOLDER:
                raise ConfigurationValidationError(
                    message=(
                        "Production environment must override default placeholder secret_key."
                    ),
                    details={"secret_key": "***DEFAULT_PLACEHOLDER***"},
                )

    def redacted(self) -> dict[str, Any]:
        """Return a nested dictionary representation with all secret values masked."""
        data = self.model_dump()
        self._mask_secrets(data)
        return data

    def safe_dict(self) -> dict[str, Any]:
        """Alias for redacted() dictionary representation."""
        return self.redacted()

    @classmethod
    def _mask_secrets(cls, obj: Any) -> None:
        """Recursively mask SecretStr and sensitive keys in a dictionary."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, SecretStr):
                    obj[key] = "***REDACTED***"
                elif isinstance(key, str) and any(
                    s in key.lower() for s in ["secret", "password", "token", "key", "credential"]
                ):
                    obj[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    cls._mask_secrets(value)
        elif isinstance(obj, list):
            for item in obj:
                cls._mask_secrets(item)
