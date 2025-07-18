"""
List boards command for showing available board mappings.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..constants import BOARD_MAPPINGS, BOARD_DESCRIPTIONS

console = Console()


def list_boards_command():
    """List common STM32 board mappings for PlatformIO."""
    
    console.print(Panel.fit(
        "[bold blue]Common STM32 Board Mappings[/bold blue]",
        border_style="blue"
    ))
    
    table = Table(title="MCU to PlatformIO Board Mappings")
    table.add_column("MCU", style="cyan")
    table.add_column("PlatformIO Board", style="magenta")
    table.add_column("Description", style="dim")
    
    for mcu, board in BOARD_MAPPINGS.items():
        description = BOARD_DESCRIPTIONS.get(board, "")
        table.add_row(mcu, board, description)
    
    console.print(table)
    
    console.print("\n[dim]Note: If your board is not listed, you can:[/dim]")
    console.print("[dim]1. Use a similar board from the same MCU family[/dim]")
    console.print("[dim]2. Check PlatformIO documentation for more boards[/dim]")
    console.print("[dim]3. Use a generic board configuration[/dim]")
