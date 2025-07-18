"""
CLI commands for STM32Bridge.
"""

from .migrate import migrate_command
from .analyze import analyze_command
from .list_boards import list_boards_command

__all__ = [
    "migrate_command",
    "analyze_command", 
    "list_boards_command"
]
