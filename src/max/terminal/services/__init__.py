"""Services package for Module 18 — Terminal Agent."""

from max.terminal.services.terminal_service import TerminalService
from max.terminal.services.tool_integration import register_terminal_tools

__all__ = [
    "TerminalService",
    "register_terminal_tools",
]
