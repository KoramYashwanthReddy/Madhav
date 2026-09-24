"""Terminal backends package for Module 18 — Terminal Agent."""

from max.terminal.backends.base import TerminalBackend
from max.terminal.backends.mock import MockTerminalBackend
from max.terminal.backends.windows import WindowsTerminalBackend
from max.terminal.backends.wsl import WSLTerminalBackend

__all__ = [
    "TerminalBackend",
    "WindowsTerminalBackend",
    "WSLTerminalBackend",
    "MockTerminalBackend",
]
