"""
Main CLI application and commands.
"""

import json
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
    board: Optional[str] = typer.Option(None, "--board", "-b", help="Board name (existing PlatformIO board or custom board name)"),
    board_file: Optional[str] = typer.Option(None, "--board-file", help="Path to custom board JSON file to copy to project"),
    board_source: Optional[str] = typer.Option(None, "--board-source", help="Source for custom board: URL, PDF file path, or board.json file path"),
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
        
        # Step 2: Handle custom board generation/detection
        board_config = None
        custom_board_file = None
        custom_board_file_to_copy = None
        
        # First, check if board_file is provided for copying existing custom board
        if board_file:
            if not board:
                console.print("[red]--board is required when using --board-file[/red]")
                raise typer.Exit(1)
            
            board_file_path = Path(board_file)
            if not board_file_path.exists():
                console.print(f"[red]Board file not found: {board_file}[/red]")
                raise typer.Exit(1)
            
            if not _is_custom_board_file(board_file_path):
                console.print(f"[red]Invalid board file format: {board_file}[/red]")
                raise typer.Exit(1)
            
            try:
                with open(board_file_path, 'r') as f:
                    board_config = json.load(f)
                custom_board_file_to_copy = board_file_path
                console.print(f"[green]✅ Custom board file '{board_file}' will be copied to project[/green]")
                
            except Exception as e:
                console.print(f"[red]Failed to load board file: {e}[/red]")
                raise typer.Exit(1)
        
        # Second, check if board_source is provided for generating new custom board
        elif board_source:
            if not board:
                console.print("[red]--board is required when using --board-source[/red]")
                raise typer.Exit(1)
            
            try:
                board_config = _generate_custom_board_from_source(board, board_source)
                console.print(f"[green]✅ Custom board '{board}' will be generated[/green]")
                
            except Exception as e:
                console.print(f"[red]Failed to generate board from source: {e}[/red]")
                raise typer.Exit(1)
        
        # Third, check if we're using a custom board that already exists
        elif board and not _is_builtin_board(board):
            custom_board_file = _find_custom_board_file(board)
            if custom_board_file:
                console.print(f"[blue]📋 Found custom board file: {custom_board_file}[/blue]")
                try:
                    with open(custom_board_file, 'r', encoding='utf-8') as f:
                        board_config = json.load(f)
                    console.print(f"[green]✅ Custom board '{board}' configuration loaded[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Could not load custom board file: {e}[/yellow]")
                    console.print(f"[yellow]Proceeding with standard board '{board}'[/yellow]")
            else:
                console.print(f"[yellow]⚠️  Custom board '{board}' not found. Proceeding as standard board.[/yellow]")
                console.print(f"[yellow]If this should be a custom board, use --board-source to generate it.[/yellow]")
        
        # Step 3: Determine board name (if not using custom board)
        if not board:
            mcu_name = project_info.get('mcu_name', project_info.get('mcu_target', ''))
            board = detect_board_name(mcu_name)
            
            if board.startswith('generic'):
                # Automatically check for custom boards in current directory
                detected_custom_board = None
                current_dir = Path.cwd()
                
                # Look for custom board files in the current directory
                for json_file in current_dir.glob("*.json"):
                    if _is_custom_board_file(json_file):
                        board_name = json_file.stem
                        console.print(f"[blue]🔍 Auto-detected custom board: {board_name}[/blue]")
                        detected_custom_board = board_name
                        # Store the source file path for later copying
                        custom_board_source_file = json_file
                        break
                
                if detected_custom_board:
                    board = detected_custom_board
                    console.print(f"[green]✅ Using auto-detected custom board: {board}[/green]")
                else:
                    board = Prompt.ask(
                        "Enter PlatformIO board name", 
                        default=board,
                        show_default=True
                    )
        
        progress.update(task, advance=10, description="Setting up PlatformIO project...")
        
        # Step 4: Create PlatformIO project
        try:
            # Override no_freertos if framework_freertos is requested
            if framework_freertos:
                no_freertos = True
                
            generator = PlatformIOProjectGenerator(output_path, project_info, no_freertos, disable_freertos)
            generator.create_project_structure()
            generator.write_platformio_ini(board)
            
            # Add custom board file if generated, found locally, copied, or auto-detected
            if (board_source and board_config) or (custom_board_file and board_config) or (custom_board_file_to_copy and board_config):
                console.print(f"[blue]📋 Adding custom board to project...[/blue]")
                from ..utils.board_generator import BoardFileGenerator
                board_generator = BoardFileGenerator()
                board_generator.create_boards_dir_structure(output_path, board, board_config)
                if custom_board_file_to_copy:
                    console.print(f"[green]✅ Custom board '{board}' copied from '{custom_board_file_to_copy}' and integrated into PlatformIO project[/green]")
                else:
                    console.print(f"[green]✅ Custom board '{board}' integrated into PlatformIO project[/green]")
            elif 'custom_board_source_file' in locals():
                # Handle auto-detected custom board file
                console.print(f"[blue]📋 Adding auto-detected custom board to project...[/blue]")
                try:
                    with open(custom_board_source_file, 'r') as f:
                        auto_detected_board_config = json.load(f)
                    
                    from ..utils.board_generator import BoardFileGenerator
                    board_generator = BoardFileGenerator()
                    board_generator.create_boards_dir_structure(output_path, board, auto_detected_board_config)
                    console.print(f"[green]✅ Auto-detected custom board '{board}' integrated into PlatformIO project[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️  Could not integrate auto-detected custom board: {e}[/yellow]")
            
            progress.update(task, advance=30, description="Migrating files...")
            
        except Exception as e:
            console.print(f"[red]Project generation failed: {e}[/red]")
            raise typer.Exit(1)
        
        # Step 5: Migrate files
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
    
    # Important note about HAL configuration and custom boards
    console.print("\n[yellow]⚠️  Important Notes:[/yellow]")
    console.print("• PlatformIO uses framework HAL drivers (not the copied CubeMX ones)")
    console.print("• Your HAL configuration (stm32l4xx_hal_conf.h) has been preserved")
    console.print("• If you have custom HAL modifications, you may need to adjust them")
    
    if board_config or 'custom_board_source_file' in locals() or custom_board_file_to_copy:
        console.print(f"• Custom board '{board}' has been integrated into the project")
        console.print("• Board configuration is available in boards/ directory")
        console.print("• PlatformIO will automatically use the custom board definition")
    
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


def _generate_custom_board_from_source(board_name: str, source: str) -> dict:
    """
    Generate a custom board configuration from various sources.
    
    Args:
        board_name: Name for the board
        source: Can be URL, PDF path, or existing board.json path
        
    Returns:
        Board configuration dictionary
    """
    from pathlib import Path
    from ..utils.mcu_scraper import STM32Scraper
    from ..utils.board_generator import BoardFileGenerator
    
    source_path = Path(source)
    
    # Determine source type and handle accordingly
    if source.startswith(('http://', 'https://')):
        # URL source - scrape from web
        console.print(f"[blue]🔧 Generating board from URL: {source}[/blue]")
        scraper = STM32Scraper()
        specs = scraper.scrape_from_url(source)
        
        if not specs:
            raise STM32MigrationError("Failed to extract MCU specifications from URL")
        
        generator = BoardFileGenerator()
        return generator.generate_board_file(specs, board_name)
        
    elif source_path.exists():
        if source_path.suffix.lower() == '.json':
            # Existing board.json file
            console.print(f"[blue]📄 Loading existing board file: {source}[/blue]")
            with open(source_path, 'r', encoding='utf-8') as f:
                board_config = json.load(f)
            console.print(f"[green]✅ Loaded existing board configuration[/green]")
            return board_config
            
        elif source_path.suffix.lower() == '.pdf':
            # PDF datasheet
            console.print(f"[blue]📄 Extracting specifications from PDF: {source}[/blue]")
            
            # Import PDF processing
            try:
                from ..cli.generate_board import _generate_from_pdf
                from rich.progress import Progress, SpinnerColumn, TextColumn
                
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                    specs = _generate_from_pdf(progress, str(source_path))
                
                if not specs:
                    raise STM32MigrationError("Failed to extract MCU specifications from PDF")
                
                generator = BoardFileGenerator()
                return generator.generate_board_file(specs, board_name)
                
            except ImportError:
                raise STM32MigrationError(
                    "PDF processing requires additional packages. Install with: uv pip install 'stm32bridge[pdf]'"
                )
        else:
            raise STM32MigrationError(f"Unsupported file type: {source_path.suffix}")
    else:
        raise STM32MigrationError(f"Source not found: {source}")


def _is_custom_board_file(file_path: Path) -> bool:
    """
    Check if a JSON file is likely a custom board file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        True if the file appears to be a custom board file
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check for typical board file structure
        required_keys = ['name', 'build', 'upload', 'frameworks']
        has_required_keys = all(key in data for key in required_keys)
        
        # Check for board-specific build properties
        has_build_props = isinstance(data.get('build'), dict) and \
                         any(key in data['build'] for key in ['mcu', 'f_cpu', 'variant'])
        
        return has_required_keys and has_build_props
    except (json.JSONDecodeError, IOError):
        return False


def _is_builtin_board(board_name: str) -> bool:
    """
    Check if a board name is a built-in PlatformIO board.
    
    This is a simple heuristic - built-in boards typically don't contain custom prefixes.
    We consider boards with 'custom' prefix or certain patterns as custom boards.
    """
    if not board_name:
        return True
        
    # Simple heuristics for detecting custom boards
    custom_indicators = [
        'custom_',
        '_custom',
        'diy_',
        'local_',
        'generated_',
    ]
    
    for indicator in custom_indicators:
        if indicator in board_name.lower():
            return False
    
    # Additional check - if board name ends with a specific MCU part number pattern
    import re
    if re.match(r'.*stm32[a-z]\d+[a-z]*\d*', board_name.lower()):
        return False
    
    return True


def _find_custom_board_file(board_name: str) -> Optional[Path]:
    """
    Find a custom board file in common locations.
    
    Searches in:
    1. Current directory: {board_name}.json
    2. boards/ subdirectory: boards/{board_name}.json  
    3. Current directory with 'board' suffix: {board_name}_board.json
    """
    from pathlib import Path
    
    possible_locations = [
        Path(f"{board_name}.json"),
        Path("boards") / f"{board_name}.json",
        Path(f"{board_name}_board.json"),
        Path("boards") / f"{board_name}_board.json",
    ]
    
    for location in possible_locations:
        if location.exists() and location.is_file():
            return location
    
    return None
