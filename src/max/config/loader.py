"""Configuration loading helpers and environment resolution strategy."""

import os
from pathlib import Path

from max.config.enums import Environment
from max.config.settings import Settings, clear_settings_cache


def load_settings(
    env_file: str | Path | None = ".env",
    environment_override: Environment | str | None = None,
) -> Settings:
    """Load settings with optional environment file and runtime environment overrides."""
    if environment_override is not None:
        os.environ["MAX_APPLICATION__ENVIRONMENT"] = str(environment_override)

    clear_settings_cache()

    if env_file and Path(env_file).exists():
        settings = Settings(_env_file=str(env_file))  # type: ignore[call-arg]
    else:
        settings = Settings(_env_file=None)  # type: ignore[call-arg]

    return settings


def get_current_environment() -> Environment:
    """Resolve active environment from environment variables or active settings."""
    env_str = os.getenv(
        "MAX_APPLICATION__ENVIRONMENT",
        os.getenv("MAX_ENVIRONMENT", "development"),
    )
    try:
        return Environment(env_str.lower())
    except ValueError:
        return Environment.DEVELOPMENT
