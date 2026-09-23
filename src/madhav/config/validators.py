"""Configuration validators and sanity checks for MADHAV configuration."""

from madhav.config.enums import Environment
from madhav.config.errors import ConfigurationError
from madhav.config.sections import (
    ApplicationSettings,
    CORSSettings,
    LoggingSettings,
    SecuritySettings,
    ServerSettings,
)


def validate_server_settings(server: ServerSettings) -> None:
    """Validate HTTP server network configuration."""
    if not (1 <= server.port <= 65535):
        raise ConfigurationError(
            f"Invalid server port: {server.port}. Port must be between 1 and 65535.",
            details={"port": server.port},
        )
    if server.workers < 1:
        raise ConfigurationError(
            f"Invalid worker count: {server.workers}. Must be at least 1.",
            details={"workers": server.workers},
        )


def validate_logging_settings(logging_cfg: LoggingSettings) -> None:
    """Validate logging level and formatting settings."""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if str(logging_cfg.level).upper() not in valid_levels:
        raise ConfigurationError(
            f"Invalid log level: {logging_cfg.level}. Must be one of {sorted(valid_levels)}.",
            details={"level": str(logging_cfg.level)},
        )


def validate_production_settings(
    app_cfg: ApplicationSettings,
    sec_cfg: SecuritySettings,
    cors_cfg: CORSSettings,
) -> None:
    """Enforce strict security validation boundaries for production deployments."""
    if app_cfg.environment == Environment.PRODUCTION:
        if app_cfg.debug:
            raise ConfigurationError(
                "Production environment violation: debug mode cannot be enabled in production.",
                details={"environment": app_cfg.environment, "debug": app_cfg.debug},
            )
        if cors_cfg.enabled and cors_cfg.allow_credentials and "*" in cors_cfg.allowed_origins:
            raise ConfigurationError(
                "Production CORS violation: wildcard origin '*' is forbidden "
                "when allow_credentials is True.",
                details={"allowed_origins": cors_cfg.allowed_origins},
            )
        if not sec_cfg.allowed_hosts:
            raise ConfigurationError(
                "Production security violation: allowed_hosts list cannot be empty.",
                details={"allowed_hosts": sec_cfg.allowed_hosts},
            )
