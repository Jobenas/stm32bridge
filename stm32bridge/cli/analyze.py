"""
Analyze command for STM32CubeMX projects.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core import ProjectAnalyzer
from ..exceptions import STM32MigrationError
from ..utils import detect_board_name

console = Console()


def analyze_command(
    source: str = typer.Argument(..., help="Path to STM32CubeMX project directory"),
):
    """
    Analyze STM32CubeMX project and show configuration details.
    
    This command analyzes your STM32CubeMX project and displays the detected
    configuration without performing migration.
    """
    
    source_path = Path(source).resolve()
    
    if not source_path.exists():
        console.print(f"[red]Source directory does not exist: {source_path}[/red]")
        raise typer.Exit(1)
    
    try:
        analyzer = ProjectAnalyzer(source_path)
        project_info = analyzer.extract_mcu_info()
        
        # Display analysis results
        console.print(Panel.fit(
            "[bold blue]STM32CubeMX Project Analysis[/bold blue]",
            border_style="blue"
        ))
        
        table = Table(title="Project Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Notes", style="dim")
        
        for key, value in project_info.items():
            if isinstance(value, list):
                value_str = ", ".join(value)
            else:
                value_str = str(value)
                
            notes = ""
            if key == 'mcu_target':
                notes = "Used for -D define"
            elif key == 'hse_value':
                notes = "External crystal frequency"
            elif key == 'mcu_family':
                notes = "Determines HAL driver paths"
                
            table.add_row(key.replace('_', ' ').title(), value_str, notes)
        
        console.print(table)
        
        # Suggest board name
        mcu_name = project_info.get('mcu_name', project_info.get('mcu_target', ''))
        suggested_board = detect_board_name(mcu_name)
        
        console.print(f"\n[bold]Suggested PlatformIO board:[/bold] {suggested_board}")
        
        # Validate structure
        if analyzer.validate_project_structure():
            console.print("[green]✅ Project structure is valid for migration[/green]")
        else:
            console.print("[red]❌ Project structure issues detected[/red]")
            
    except STM32MigrationError as e:
        console.print(f"[red]Analysis failed: {e}[/red]")
        raise typer.Exit(1)
