"""PlatformDetector for detecting host operating system environment."""

import sys

from max.computer.domain.enums import PlatformType


class PlatformDetector:
    """Utility for identifying host operating system platform."""

    @staticmethod
    def detect() -> PlatformType:
        """Detect current operating system platform."""
        plat = sys.platform.lower()
        if plat.startswith("win"):
            return PlatformType.WINDOWS
        elif plat.startswith("linux"):
            return PlatformType.LINUX
        elif plat.startswith("darwin"):
            return PlatformType.MACOS
        return PlatformType.UNKNOWN
