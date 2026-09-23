"""Settings loading utilities and caching mechanism for MADHAV."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from madhav.config.enums import Environment
from madhav.config.settings import Settings


def load_settings(
    env_file: str | Path | None = None,
    env_overrides: dict[str, Any] | None = None,
) -> Settings:
    """Load, construct, and validate Settings instance.

    Loading Precedence:
    1. Built-in defaults
    2. Environment-specific defaults
    3. Local .env file (if env_file specified or found, unless in TESTING environment)
    4. Environment variables (MADHAV_*)
    5. Explicit env_overrides dictionary
    """
    kwargs: dict[str, Any] = {}

    target_env_file: Path | None = None
    if env_file is not None:
        target_env_file = Path(env_file)
    else:
        default_env = Path(".env")
        if default_env.is_file():
            target_env_file = default_env

    current_env = os.getenv("MADHAV_ENVIRONMENT", os.getenv("MADHAV_APPLICATION__ENVIRONMENT", ""))
    if current_env.lower() == Environment.TESTING and env_file is None:
        target_env_file = None

    if target_env_file is not None and target_env_file.is_file():
        kwargs["_env_file"] = target_env_file

    if env_overrides:
        for k, v in env_overrides.items():
            kwargs[k] = v

    settings = Settings(**kwargs)
    settings.validate_runtime_invariants()
    return settings


@lru_cache
def get_settings() -> Settings:
    """Retrieve global cached Settings singleton."""
    return load_settings()


def clear_settings_cache() -> None:
    """Clear the global get_settings LRU cache (for test isolation)."""
    get_settings.cache_clear()
