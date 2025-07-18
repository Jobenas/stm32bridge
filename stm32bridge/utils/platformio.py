"""
PlatformIO utilities and command execution.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from rich.console import Console

console = Console()


def check_platformio_installed() -> bool:
    """Check if PlatformIO is installed and accessible."""
    try:
        result = subprocess.run(
            ["pio", "--version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_platformio_command(command: List[str], cwd: Path) -> Tuple[bool, str, str]:
    """Run a PlatformIO command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True, result.stdout, result.stderr
    except FileNotFoundError:
        error_msg = f"PlatformIO command not found. Make sure PlatformIO is installed and in your PATH."
        console.print(f"[red]{error_msg}[/red]")
        console.print(f"[yellow]Install PlatformIO: pip install platformio[/yellow]")
        console.print(f"[yellow]Or visit: https://platformio.org/install[/yellow]")
        return False, "", error_msg
    except subprocess.CalledProcessError as e:
        error_msg = f"Command failed: {' '.join(command)}\nError: {e.stderr}"
        console.print(f"[red]Command failed: {' '.join(command)}[/red]")
        console.print(f"[red]Error: {e.stderr}[/red]")
        return False, e.stdout or "", e.stderr or ""


def install_python_dependency(package: str, cwd: Path) -> bool:
    """Install a Python package dependency."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package], 
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        console.print(f"[green]✅ Installed {package}[/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to install {package}: {e.stderr}[/red]")
        return False
