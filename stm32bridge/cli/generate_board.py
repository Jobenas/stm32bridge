"""
Board generation commands for STM32Bridge CLI.

This module provides commands for creating custom PlatformIO board files
from various sources including URLs, PDFs, manual input, and direct parameters.
"""

import json
import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm

from ..utils.mcu_scraper import STM32Scraper, MCUSpecs
from ..utils.board_generator import BoardFileGenerator
from ..exceptions import STM32MigrationError

console = Console()

def generate_board(
    name: str = typer.Argument(..., help="Name for the generated board file"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Source: URL, PDF file, or JSON board file"),
    manual: bool = typer.Option(False, "--manual", "-m", help="Use interactive manual input"),
    part_number: Optional[str] = typer.Option(None, "--part-number", help="MCU part number (e.g., STM32L432KC)"),
    core: Optional[str] = typer.Option(None, "--core", help="ARM core (cortex-m0, cortex-m3, cortex-m4, etc.)"),
    frequency: Optional[int] = typer.Option(None, "--frequency", help="Max frequency in MHz"),
    flash_kb: Optional[int] = typer.Option(None, "--flash", help="Flash memory size in KB"),
    ram_kb: Optional[int] = typer.Option(None, "--ram", help="RAM size in KB"),
    voltage_min: Optional[float] = typer.Option(None, "--voltage-min", help="Minimum operating voltage"),
    voltage_max: Optional[float] = typer.Option(None, "--voltage-max", help="Maximum operating voltage"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory for board file"),
    project: Optional[Path] = typer.Option(None, "--project", "-p", help="PlatformIO project path to add board to"),
) -> None:
    """
    Generate a custom PlatformIO board file using multiple input methods.
    
    This command supports various ways to create board configurations:
    
    \b
    📡 URL Scraping:
        stm32bridge generate-board my_board --source "https://www.st.com/en/.../stm32l432kc.html"
        stm32bridge generate-board my_board --source "https://www.mouser.com/ProductDetail/STMicroelectronics/STM32F103C8T6?..."
    
    \b
    📄 PDF Datasheet:
        stm32bridge generate-board my_board --source ./stm32l432kc_datasheet.pdf
    
    \b
    📄 Existing Board File:
        stm32bridge generate-board my_board --source ./existing_board.json
    
    \b
    ⌨️  Manual Input:
        stm32bridge generate-board my_board --manual
    
    \b
    🎯 Direct Parameters:
        stm32bridge generate-board my_board --part-number STM32L432KC --core cortex-m4 --frequency 80 --flash 256 --ram 64
    
    \b
    🏗️ Add to Project:
        stm32bridge generate-board my_board --source "..." --project ./my_platformio_project
    """
    console.print(f"[blue]🔧 STM32Bridge Board Generator v1.2.0[/blue]")
    console.print(f"[blue]Generating board file '{name}'...[/blue]\n")
    
    # Validate input options
    input_methods = sum([bool(source), manual, bool(part_number)])
    if input_methods == 0:
        console.print("[red]❌ Error: Please specify an input method:[/red]")
        console.print("[yellow]  --source <URL/file>   Scrape from URL or extract from file[/yellow]")
        console.print("[yellow]  --manual              Interactive input[/yellow]")
        console.print("[yellow]  --part-number <n>  Direct parameters[/yellow]")
        raise typer.Exit(1)
    elif input_methods > 1:
        console.print("[red]❌ Error: Please use only one input method at a time[/red]")
        raise typer.Exit(1)
    
    # Additional validation for source parameter
    if source:
        source_path = Path(source)
        if not (source.startswith(('http://', 'https://')) or source_path.exists()):
            console.print(f"[red]❌ Error:[/red] Source not found: {source}")
            console.print("Source must be a valid URL or existing file path")
            raise typer.Exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Step 1: Get MCU specifications based on input method
            if source:
                # Determine source type and call appropriate handler
                if source.startswith(('http://', 'https://')):
                    specs = _generate_from_url(progress, source)
                elif source.lower().endswith('.pdf'):
                    specs = _generate_from_pdf(progress, source)
                elif source.lower().endswith('.json'):
                    # Handle existing board file
                    specs = _load_from_json_file(progress, source)
                else:
                    console.print(f"[red]❌ Error:[/red] Unsupported source type: {source}")
                    console.print("Source must be a URL, PDF file, or JSON file")
                    raise typer.Exit(1)
            elif manual:
                specs = _generate_from_manual_input(progress, name)
            else:  # Direct parameters
                specs = _generate_from_parameters(progress, part_number, core, frequency, flash_kb, ram_kb, voltage_min, voltage_max)
            
            # Step 2: Generate board file
            if not specs:
                console.print("[red]❌ Failed to generate MCU specifications[/red]")
                raise typer.Exit(1)
            
            task = progress.add_task("Generating board file...", total=None)
            generator = BoardFileGenerator()
            board_config = generator.generate_board_file(specs, name)
            
            # Step 3: Save board file
            if project:
                # Add to existing PlatformIO project
                boards_dir = project / "boards"
                boards_dir.mkdir(exist_ok=True)
                output_file = boards_dir / f"{name}.json"
                console.print(f"[green]📁 Adding board to project: {project}[/green]")
            else:
                # Save to specified output directory or current directory
                output_dir = output or Path.cwd()
                output_file = output_dir / f"{name}.json"
                console.print(f"[green]📁 Saving to: {output_dir}[/green]")
            
            progress.update(task, description="Writing board file...")
            with open(output_file, 'w') as f:
                json.dump(board_config, f, indent=2)
            
            progress.remove_task(task)
            
            console.print(f"[green]✅ Board file '{name}.json' generated successfully![/green]")
            console.print(f"[blue]📍 Location: {output_file.absolute()}[/blue]")
            
            # Show usage instructions
            console.print("\n[yellow]📋 Usage Instructions:[/yellow]")
            console.print(f"[white]1. Copy {name}.json to your PlatformIO project's boards/ directory[/white]")
            console.print(f"[white]2. Set board = {name} in your platformio.ini[/white]")
            console.print(f"[white]3. Run: pio run to build your project[/white]")

    except STM32MigrationError as e:
        console.print(f"[red]❌ STM32Bridge Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


def _generate_from_url(progress: Progress, url: str) -> Optional[MCUSpecs]:
    """Generate MCU specs from URL scraping."""
    task = progress.add_task("Scraping MCU data from URL...", total=None)
    scraper = STM32Scraper()  # Create scraper outside try block
    
    try:
        specs = scraper.scrape_from_url(url)
        progress.remove_task(task)
        
        if specs:
            console.print(f"[green]✅ Successfully scraped: {specs.part_number}[/green]")
            console.print(f"[blue]📊 Core: {specs.core} | Freq: {specs.max_frequency} | Flash: {specs.flash_size_kb}KB | RAM: {specs.ram_size_kb}KB[/blue]")
        
        return specs
    except Exception as e:
        progress.remove_task(task)
        console.print(f"[red]❌ URL scraping failed: {e}[/red]")
        
        # Try to extract part number from URL as fallback
        import re
        url_match = re.search(r'stm32([a-z]\d+[a-z]*\d*)', url.lower())
        if url_match:
            part_number = f"STM32{url_match.group(1).upper()}"
            console.print(f"[yellow]🔄 Attempting fallback with part number: {part_number}[/yellow]")
            
            fallback_task = progress.add_task("Creating basic specs from part number...", total=None)
            fallback_specs = scraper.create_from_part_number(part_number)
            progress.remove_task(fallback_task)
            
            if fallback_specs:
                console.print(f"[green]✅ Created basic specs for: {fallback_specs.part_number}[/green]")
                console.print(f"[blue]📊 Core: {fallback_specs.core} | Freq: {fallback_specs.max_frequency} | Flash: {fallback_specs.flash_size_kb}KB | RAM: {fallback_specs.ram_size_kb}KB[/blue]")
                return fallback_specs
        
        return None


def _generate_from_pdf(progress: Progress, pdf_path: str) -> Optional[MCUSpecs]:
    """Generate MCU specs from PDF datasheet."""
    task = progress.add_task("Extracting data from PDF...", total=None)
    
    try:
        # Check if PDF libraries are available
        try:
            import PyPDF2
            import pdfplumber
        except ImportError:
            progress.remove_task(task)
            console.print("[red]❌ PDF processing requires additional dependencies[/red]")
            console.print("[yellow]Install with: pip install PyPDF2 pdfplumber[/yellow]")
            return None
        
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            progress.remove_task(task)
            console.print(f"[red]❌ PDF file not found: {pdf_path}[/red]")
            return None
        
        # Try to extract text and find MCU specs
        with pdfplumber.open(pdf_file) as pdf:
            text_content = ""
            # Extract text from first few pages (likely to contain specs)
            for page_num in range(min(5, len(pdf.pages))):
                page = pdf.pages[page_num]
                text_content += page.extract_text() or ""
        
        # Use STM32Scraper to parse the extracted text
        # TODO: Implement text parsing method in STM32Scraper
        console.print("[yellow]⚠️  PDF text parsing not yet implemented[/yellow]")
        console.print("[yellow]Please use --manual mode for interactive input[/yellow]")
        specs = None
        
        progress.remove_task(task)
        
        if specs:
            console.print(f"[green]✅ Successfully extracted: {specs.part_number}[/green]")
            console.print(f"[blue]📊 Core: {specs.core} | Freq: {specs.max_frequency}MHz | Flash: {specs.flash_size_kb}KB | RAM: {specs.ram_size_kb}KB[/blue]")
        else:
            console.print("[yellow]⚠️  Could not extract complete MCU specifications from PDF[/yellow]")
            console.print("[yellow]Try using --manual mode for interactive input[/yellow]")
        
        return specs
    except Exception as e:
        progress.remove_task(task)
        console.print(f"[red]❌ PDF processing failed: {e}[/red]")
        return None


def _load_from_json_file(progress: Progress, json_path: str) -> Optional[MCUSpecs]:
    """Load MCU specs from existing JSON board file."""
    task = progress.add_task("Loading from JSON file...", total=None)
    
    try:
        json_file = Path(json_path)
        if not json_file.exists():
            progress.remove_task(task)
            console.print(f"[red]❌ JSON file not found: {json_path}[/red]")
            return None
        
        with open(json_file, 'r') as f:
            board_data = json.load(f)
        
        # Extract MCU specs from board file
        specs = MCUSpecs(
            part_number=board_data.get('build', {}).get('mcu', 'Unknown'),
            family='STM32L4',  # Default family
            core=board_data.get('build', {}).get('cpu', 'cortex-m4'),
            max_frequency=str(board_data.get('build', {}).get('f_cpu', 80000000) // 1000000),  # Convert to MHz string
            flash_size_kb=board_data.get('upload', {}).get('maximum_size', 256000) // 1024,  # Convert to KB
            ram_size_kb=board_data.get('upload', {}).get('maximum_ram_size', 64000) // 1024,  # Convert to KB
            package='LQFP',  # Default package
            pin_count=64,  # Default pin count
            operating_voltage_min=board_data.get('build', {}).get('voltage_min', 1.8),
            operating_voltage_max=board_data.get('build', {}).get('voltage_max', 3.6),
            temperature_min=-40,  # Default temperature range
            temperature_max=85,
            peripherals={},  # Empty peripherals
            features=[],  # Empty features
        )
        
        progress.remove_task(task)
        console.print(f"[green]✅ Successfully loaded: {specs.part_number}[/green]")
        console.print(f"[blue]📊 Core: {specs.core} | Freq: {specs.max_frequency}MHz | Flash: {specs.flash_size_kb}KB | RAM: {specs.ram_size_kb}KB[/blue]")
        
        return specs
    except Exception as e:
        progress.remove_task(task)
        console.print(f"[red]❌ JSON loading failed: {e}[/red]")
        return None


def _generate_from_manual_input(progress: Progress, board_name: str) -> Optional[MCUSpecs]:
    """Generate MCU specs from interactive user input."""
    console.print(f"\n[blue]🎯 Manual Input Mode - Creating board '{board_name}'[/blue]")
    console.print("[yellow]Please provide the following MCU specifications:[/yellow]\n")
    
    try:
        # Get MCU part number
        part_number = Prompt.ask(
            "[cyan]MCU Part Number[/cyan] (e.g., STM32L432KC)",
            default="STM32L432KC"
        ).upper()
        
        # Get ARM core
        core_options = ["cortex-m0", "cortex-m0plus", "cortex-m3", "cortex-m4", "cortex-m7", "cortex-m33"]
        console.print(f"[cyan]ARM Core Options:[/cyan] {', '.join(core_options)}")
        core = Prompt.ask(
            "[cyan]ARM Core[/cyan]",
            default="cortex-m4",
            choices=core_options
        )
        
        # Get frequency
        frequency = IntPrompt.ask(
            "[cyan]Maximum Frequency[/cyan] (MHz)",
            default=80
        )
        
        # Get flash size
        flash_size = IntPrompt.ask(
            "[cyan]Flash Memory Size[/cyan] (KB)",
            default=256
        )
        
        # Get RAM size
        ram_size = IntPrompt.ask(
            "[cyan]RAM Size[/cyan] (KB)",
            default=64
        )
        
        # Get voltage range
        voltage_min = FloatPrompt.ask(
            "[cyan]Minimum Operating Voltage[/cyan] (V)",
            default=1.8
        )
        
        voltage_max = FloatPrompt.ask(
            "[cyan]Maximum Operating Voltage[/cyan] (V)",
            default=3.6
        )
        
        # Create MCU specs
        specs = MCUSpecs(
            part_number=part_number,
            family='STM32L4',  # Default family
            core=core,
            max_frequency=str(frequency),  # Convert to string
            flash_size_kb=flash_size,
            ram_size_kb=ram_size,
            package='LQFP',  # Default package
            pin_count=64,  # Default pin count
            operating_voltage_min=voltage_min,
            operating_voltage_max=voltage_max,
            temperature_min=-40,  # Default temperature range
            temperature_max=85,
            peripherals={},  # Empty peripherals
            features=[],  # Empty features
        )
        
        # Confirm with user
        console.print(f"\n[green]📋 MCU Specification Summary:[/green]")
        console.print(f"[blue]Part Number:[/blue] {specs.part_number}")
        console.print(f"[blue]ARM Core:[/blue] {specs.core}")
        console.print(f"[blue]Max Frequency:[/blue] {specs.max_frequency} MHz")
        console.print(f"[blue]Flash Size:[/blue] {specs.flash_size_kb} KB")
        console.print(f"[blue]RAM Size:[/blue] {specs.ram_size_kb} KB")
        console.print(f"[blue]Voltage Range:[/blue] {specs.operating_voltage_min}V - {specs.operating_voltage_max}V")
        
        if Confirm.ask("\n[cyan]Are these specifications correct?[/cyan]", default=True):
            console.print("[green]✅ Manual input completed[/green]")
            return specs
        else:
            console.print("[yellow]⚠️  Manual input cancelled[/yellow]")
            return None
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Manual input cancelled by user[/yellow]")
        return None
    except Exception as e:
        console.print(f"\n[red]❌ Manual input failed: {e}[/red]")
        return None


def _generate_from_parameters(
    progress: Progress,
    part_number: str,
    core: Optional[str],
    frequency: Optional[int],
    flash_kb: Optional[int],
    ram_kb: Optional[int],
    voltage_min: Optional[float],
    voltage_max: Optional[float]
) -> Optional[MCUSpecs]:
    """Generate MCU specs from direct command-line parameters."""
    task = progress.add_task("Processing direct parameters...", total=None)
    
    try:
        # Validate required parameters
        if not part_number:
            progress.remove_task(task)
            console.print("[red]❌ Part number is required for direct parameter mode[/red]")
            return None
        
        # Apply defaults for missing parameters
        specs = MCUSpecs(
            part_number=part_number.upper(),
            family='STM32L4',  # Default family
            core=core or "cortex-m4",
            max_frequency=str(frequency or 80),  # Convert to string
            flash_size_kb=flash_kb or 256,
            ram_size_kb=ram_kb or 64,
            package='LQFP',  # Default package
            pin_count=64,  # Default pin count
            operating_voltage_min=voltage_min or 1.8,
            operating_voltage_max=voltage_max or 3.6,
            temperature_min=-40,  # Default temperature range
            temperature_max=85,
            peripherals={},  # Empty peripherals
            features=[],  # Empty features
        )
        
        progress.remove_task(task)
        console.print(f"[green]✅ Direct parameters processed: {specs.part_number}[/green]")
        console.print(f"[blue]📊 Core: {specs.core} | Freq: {specs.max_frequency}MHz | Flash: {specs.flash_size_kb}KB | RAM: {specs.ram_size_kb}KB[/blue]")
        
        return specs
    except Exception as e:
        progress.remove_task(task)
        console.print(f"[red]❌ Parameter processing failed: {e}[/red]")
        return None
