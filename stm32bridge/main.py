#!/usr/bin/env python3
"""
STM32Bridge - STM32CubeMX to PlatformIO Migration Tool

Main entry point for the CLI application.
"""

import typer
from typing import Optional

from stm32bridge import __version__
from stm32bridge.cli import migrate_command, analyze_command, list_boards_command
from stm32bridge.cli.generate_board import generate_board

def version_callback(value: bool):
    if value:
        typer.echo(f"STM32Bridge version {__version__}")
        raise typer.Exit()

app = typer.Typer(
    name="stm32bridge",
    help="Migrate STM32CubeMX projects to PlatformIO",
    add_completion=False,
)

# Register commands
app.command("migrate", help="Migrate STM32CubeMX project to PlatformIO.")(migrate_command)
app.command("analyze", help="Analyze STM32CubeMX project and show configuration details.")(analyze_command)
app.command("list-boards", help="List common STM32 board mappings for PlatformIO.")(list_boards_command)
app.command("generate-board", help="Generate custom PlatformIO board file from STM32 product URL.")(generate_board)

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", 
        callback=version_callback, 
        is_eager=True,
        help="Show version and exit"
    )
):
    """
    STM32Bridge - STM32CubeMX to PlatformIO Migration Tool
    
    Migrate your STM32CubeMX projects to PlatformIO with ease!
    """
    return


if __name__ == "__main__":
    app()
