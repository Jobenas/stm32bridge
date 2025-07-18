"""
Main CLI application and commands.
"""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..core import ProjectAnalyzer, PlatformIOProjectGenerator, FileMigrator
from ..exceptions import STM32MigrationError
from ..utils import (
    verify_and_build_project,
    open_project_in_editor,
    detect_board_name
)

console = Console()


def migrate_command(
    source: str = typer.Argument(..., help="Path to STM32CubeMX project directory"),
    output: str = typer.Argument(..., help="Path for output PlatformIO project"),
    board: Optional[str] = typer.Option(None, "--board", "-b", help="PlatformIO board name"),
    build: bool = typer.Option(False, "--build", help="Build and verify project after migration"),
    open_editor: bool = typer.Option(False, "--open", "-o", help="Open project in code editor after successful migration"),
    editor: str = typer.Option("code", "--editor", help="Code editor to open (default: 'code' for VS Code)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing output directory"),
    no_freertos: bool = typer.Option(False, "--no-freertos", help="Skip FreeRTOS library dependency (use framework FreeRTOS)"),
    disable_freertos: bool = typer.Option(False, "--disable-freertos", help="Completely disable FreeRTOS migration (manual setup required)"),
    framework_freertos: bool = typer.Option(False, "--framework-freertos", help="Use PlatformIO framework's built-in FreeRTOS support"),
):
    """
    Migrate STM32CubeMX project to PlatformIO.
    
    This command analyzes your STM32CubeMX project, extracts the configuration,
    and creates a new PlatformIO project with all the necessary files and settings.
    """
    
    console.print(Panel.fit(
        "[bold blue]STM32CubeMX to PlatformIO Migration Tool[/bold blue]",
        border_style="blue"
    ))
    
    # Validate paths
    source_path = Path(source).resolve()
    output_path = Path(output).resolve()
    
    if not source_path.exists():
        console.print(f"[red]Source directory does not exist: {source_path}[/red]")
        raise typer.Exit(1)
        
    if output_path.exists() and not force:
        if not Confirm.ask(f"Output directory exists: {output_path}. Overwrite?"):
            console.print("[yellow]Migration cancelled[/yellow]")
            raise typer.Exit(0)
        shutil.rmtree(output_path)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    with Progress() as progress:
        task = progress.add_task("Analyzing project...", total=100)
        
        # Step 1: Analyze source project
        try:
            analyzer = ProjectAnalyzer(source_path)
            if not analyzer.validate_project_structure():
                console.print("[red]Invalid project structure. Make sure to generate with 'Makefile' toolchain.[/red]")
                raise typer.Exit(1)
            
            project_info = analyzer.extract_mcu_info()
            progress.update(task, advance=20, description="Extracting configuration...")
            
        except STM32MigrationError as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            raise typer.Exit(1)
        
        # Display project information
        table = Table(title="Detected Project Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        for key, value in project_info.items():
            if isinstance(value, list):
                value = ", ".join(value)
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        console.print(table)
        
        # Step 2: Determine board name
        if not board:
            mcu_name = project_info.get('mcu_name', project_info.get('mcu_target', ''))
            board = detect_board_name(mcu_name)
            
            if board.startswith('generic'):
                board = Prompt.ask(
                    "Enter PlatformIO board name", 
                    default=board,
                    show_default=True
                )
        
        progress.update(task, advance=10, description="Setting up PlatformIO project...")
        
        # Step 3: Create PlatformIO project
        try:
            # Override no_freertos if framework_freertos is requested
            if framework_freertos:
                no_freertos = True
                
            generator = PlatformIOProjectGenerator(output_path, project_info, no_freertos, disable_freertos)
            generator.create_project_structure()
            generator.write_platformio_ini(board)
            progress.update(task, advance=30, description="Migrating files...")
            
        except Exception as e:
            console.print(f"[red]Project generation failed: {e}[/red]")
            raise typer.Exit(1)
        
        # Step 4: Migrate files
        try:
            migrator = FileMigrator(source_path, output_path, disable_freertos=disable_freertos)
            migrator.migrate_all_files()
            progress.update(task, advance=30, description="Finalizing...")
            
        except Exception as e:
            console.print(f"[red]File migration failed: {e}[/red]")
            raise typer.Exit(1)
        
        progress.update(task, advance=10, description="Migration complete!")
    
    console.print(f"[green]✅ Migration completed successfully![/green]")
    console.print(f"[blue]Output directory: {output_path}[/blue]")
    
    # Important note about HAL configuration
    console.print("\n[yellow]⚠️  Important Notes:[/yellow]")
    console.print("• PlatformIO uses framework HAL drivers (not the copied CubeMX ones)")
    console.print("• Your HAL configuration (stm32l4xx_hal_conf.h) has been preserved")
    console.print("• If you have custom HAL modifications, you may need to adjust them")
    
    if project_info.get('uses_freertos', False):
        if no_freertos:
            console.print("• FreeRTOS detected but library dependency skipped (using framework)")
            console.print("• You may need to manually configure FreeRTOS includes")
        else:
            console.print("• FreeRTOS detected - FreeRTOS-Kernel library has been added")
            console.print("• FreeRTOS configuration has been adapted for PlatformIO compatibility")
            console.print("• If build issues persist, try: --no-freertos flag")
    
    # Step 5: Optional build verification
    if build:
        console.print("\n[yellow]🔧 Building and verifying project...[/yellow]")
        build_success = verify_and_build_project(output_path, project_info)
        
        if build_success:
            console.print("[green]✅ Project verified and builds successfully![/green]")
        else:
            console.print("[red]❌ Build verification failed - but project files are ready[/red]")
            console.print("[yellow]You may need to manually resolve build issues[/yellow]")
    else:
        console.print("\n[yellow]⏭️ Skipping build verification (use --build to enable)[/yellow]")
        build_success = None
    
    # Step 6: Optional editor opening
    if open_editor:
        if build_success is False:
            console.print("[yellow]⚠️ Project has build issues, but opening editor anyway...[/yellow]")
        
        if open_project_in_editor(output_path, editor):
            console.print(f"[green]✅ Opened project in {editor}[/green]")
        else:
            console.print(f"[yellow]⚠️ Could not open {editor} - you may need to open the project manually[/yellow]")
    
    # Show next steps
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("1. cd " + str(output_path))
    if build_success:
        console.print("2. pio run -t upload # Upload to device (project already built)")
        console.print("3. pio device monitor # Monitor serial output")
    elif build_success is False:
        console.print("2. pio run          # Try building again")
        console.print("3. pio run -t upload # Upload to device") 
        console.print("4. pio device monitor # Monitor serial output")
    else:
        console.print("2. pio run          # Build the project")
        console.print("3. pio run -t upload # Upload to device")
        console.print("4. pio device monitor # Monitor serial output")
