"""
Code editor integration utilities.
"""

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def open_project_in_editor(project_path: Path, editor: str = "code") -> bool:
    """Open the project in the specified code editor."""
    try:
        # Common editor commands and their typical executable names
        editor_commands = {
            "code": ["code", str(project_path)],  # VS Code
            "vscode": ["code", str(project_path)],  # VS Code alternative name
            "codium": ["codium", str(project_path)],  # VSCodium
            "subl": ["subl", str(project_path)],  # Sublime Text
            "sublime": ["subl", str(project_path)],  # Sublime Text alternative
            "atom": ["atom", str(project_path)],  # Atom
            "notepad++": ["notepad++", str(project_path)],  # Notepad++
            "vim": ["vim", str(project_path)],  # Vim
            "nvim": ["nvim", str(project_path)],  # Neovim
            "emacs": ["emacs", str(project_path)],  # Emacs
            "gedit": ["gedit", str(project_path)],  # Gedit
            "kate": ["kate", str(project_path)],  # Kate
        }
        
        # If the editor is not in our predefined list, try to run it directly
        if editor.lower() not in editor_commands:
            command = [editor, str(project_path)]
        else:
            command = editor_commands[editor.lower()]
        
        # Try to open the editor
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10  # Don't wait too long
        )
        
        # For most editors, successful launch returns 0 even if they fork to background
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        # Editor might have opened successfully but is running in background
        console.print(f"[dim]Editor {editor} started (running in background)[/dim]")
        return True
    except FileNotFoundError:
        console.print(f"[red]Editor '{editor}' not found in PATH[/red]")
        console.print(f"[yellow]Available editors: code, codium, subl, atom, vim, emacs[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]Failed to open editor '{editor}': {e}[/red]")
        return False
