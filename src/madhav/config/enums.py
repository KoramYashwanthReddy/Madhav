"""Environment and logging enumerations for MADHAV configuration."""

from enum import StrEnum


class Environment(StrEnum):
    """Execution environment enumeration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(StrEnum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
