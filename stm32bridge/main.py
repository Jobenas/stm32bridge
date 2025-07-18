#!/usr/bin/env python3
"""
STM32Bridge - STM32CubeMX to PlatformIO Migration Tool

Main entry point for the CLI application.
"""

import typer

from stm32bridge.cli import migrate_command, analyze_command, list_boards_command

app = typer.Typer(
    name="stm32bridge",
    help="Migrate STM32CubeMX projects to PlatformIO",
    add_completion=False,
)

# Register commands
app.command("migrate", help="Migrate STM32CubeMX project to PlatformIO.")(migrate_command)
app.command("analyze", help="Analyze STM32CubeMX project and show configuration details.")(analyze_command)
app.command("list-boards", help="List common STM32 board mappings for PlatformIO.")(list_boards_command)


if __name__ == "__main__":
    app()
