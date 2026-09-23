"""Type definitions and enumerations for the MADHAV platform foundation."""

from enum import StrEnum, auto


class Environment(StrEnum):
    """Execution environment enumeration."""

    DEVELOPMENT = auto()
    STAGING = auto()
    PRODUCTION = auto()
    TESTING = auto()


class LogLevel(StrEnum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
