"""Environment enumerations for MADHAV configuration system."""

from enum import StrEnum, auto


class Environment(StrEnum):
    """Supported application execution environments."""

    DEVELOPMENT = auto()
    TESTING = auto()
    PRODUCTION = auto()
