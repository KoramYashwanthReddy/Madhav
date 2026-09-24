"""Computer control backends package."""

from max.computer.backends.base import ComputerControlBackend
from max.computer.backends.mock import MockComputerControlBackend
from max.computer.backends.platform_detector import PlatformDetector
from max.computer.backends.windows import WindowsComputerControlBackend

__all__ = [
    "ComputerControlBackend",
    "MockComputerControlBackend",
    "PlatformDetector",
    "WindowsComputerControlBackend",
]
