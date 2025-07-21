"""
Code editor integration utilities.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


def _find_vscode_windows() -> Optional[str]:
    """Find VS Code installation on Windows."""
    common_paths = [
        # VS Code installed for all users
        Path(os.environ.get('PROGRAMFILES', '')) / 'Microsoft VS Code' / 'Code.exe',
        # VS Code installed for current user
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Microsoft VS Code' / 'Code.exe',
        # VS Code Insiders
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Microsoft VS Code Insiders' / 'Code - Insiders.exe',
    ]
    
    for path in common_paths:
        if path.exists():
            return str(path)
    return None


def _find_editor_executable(editor: str) -> Optional[str]:
    """Find the executable path for the given editor."""
    # First, try to find it in PATH
    executable = shutil.which(editor)
    if executable:
        return executable
    
    # Handle special cases for Windows
    if os.name == 'nt':  # Windows
        if editor.lower() in ['code', 'vscode']:
            vscode_path = _find_vscode_windows()
            if vscode_path:
                return vscode_path
        
        # Try with .exe extension
        exe_name = f"{editor}.exe"
        executable = shutil.which(exe_name)
        if executable:
            return executable
    
    return None


def open_project_in_editor(project_path: Path, editor: str = "code") -> bool:
    """Open the project in the specified code editor."""
    try:
        # Find the editor executable
        editor_executable = _find_editor_executable(editor)
        
        if not editor_executable:
            console.print(f"[red]Editor '{editor}' not found in PATH[/red]")
            if editor.lower() in ['code', 'vscode']:
                console.print("[yellow]💡 Tip: Install VS Code or add it to your PATH[/yellow]")
                console.print("[yellow]   Download from: https://code.visualstudio.com/[/yellow]")
            console.print(f"[yellow]Available editors to try: codium, subl, atom, vim, emacs, notepad++[/yellow]")
            return False
        
        # Prepare the command
        command = [editor_executable, str(project_path)]
        
        # Try to open the editor
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10  # Don't wait too long
        )
        
        # For most editors, successful launch returns 0 even if they fork to background
        if result.returncode == 0:
            console.print(f"[green]✅ Opened project in {editor}[/green]")
            return True
        else:
            console.print(f"[red]Failed to open {editor}: {result.stderr}[/red]")
            return False
        
    except subprocess.TimeoutExpired:
        # Editor might have opened successfully but is running in background
        console.print(f"[dim]Editor {editor} started (running in background)[/dim]")
        return True
    except FileNotFoundError:
        console.print(f"[red]Editor '{editor}' not found[/red]")
        if editor.lower() in ['code', 'vscode']:
            console.print("[yellow]💡 Tip: Install VS Code or add it to your PATH[/yellow]")
            console.print("[yellow]   Download from: https://code.visualstudio.com/[/yellow]")
        console.print(f"[yellow]Available editors to try: codium, subl, atom, vim, emacs, notepad++[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]Failed to open editor '{editor}': {e}[/red]")
        return False
