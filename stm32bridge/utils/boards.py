"""
Board detection and mapping utilities.
"""

from rich.console import Console
from rich.prompt import Prompt

from ..constants import BOARD_MAPPINGS

console = Console()


def detect_board_name(mcu_name: str) -> str:
    """Detect PlatformIO board name from MCU name."""
    mcu_upper = mcu_name.upper()
    
    # Check direct mappings
    for mcu_pattern, board_name in BOARD_MAPPINGS.items():
        if mcu_upper.startswith(mcu_pattern):
            return board_name
    
    # Fallback: ask user or use generic
    console.print(f"[yellow]Could not auto-detect board for MCU: {mcu_name}[/yellow]")
    return "genericSTM32F401RE"  # Generic fallback
