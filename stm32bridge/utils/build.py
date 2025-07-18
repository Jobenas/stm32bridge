"""
Build verification and dependency management utilities.
"""

import re
from pathlib import Path
from typing import Dict

from rich.console import Console

from .platformio import check_platformio_installed, run_platformio_command, install_python_dependency

console = Console()


def verify_and_build_project(output_path: Path, project_info: Dict[str, str]) -> bool:
    """Verify project setup and build, handling any missing dependencies."""
    console.print("[yellow]🔧 Verifying project setup and building...[/yellow]")
    
    # Check PlatformIO installation
    if not check_platformio_installed():
        console.print("[red]❌ PlatformIO not found. Cannot verify build.[/red]")
        return False
    
    # Show build configuration summary
    console.print(f"[dim]Building for: {project_info.get('mcu_name', 'Unknown MCU')}[/dim]")
    if project_info.get('uses_freertos', False):
        console.print(f"[dim]FreeRTOS: Enabled[/dim]")
    
    # Attempt initial build
    success, stdout, stderr = run_platformio_command(["pio", "run"], output_path)
    
    if success:
        console.print("[green]✅ Build successful on first attempt![/green]")
        
        # Extract and show build statistics
        if "RAM:" in stdout and "Flash:" in stdout:
            ram_match = re.search(r'RAM:\s+\[.*?\]\s+([\d.]+)%\s+\(used (\d+) bytes from (\d+) bytes\)', stdout)
            flash_match = re.search(r'Flash:\s+\[.*?\]\s+([\d.]+)%\s+\(used (\d+) bytes from (\d+) bytes\)', stdout)
            
            if ram_match and flash_match:
                console.print("[dim]📊 Memory Usage:[/dim]")
                console.print(f"[dim]  RAM:   {ram_match.group(1)}% ({ram_match.group(2)} bytes)[/dim]")
                console.print(f"[dim]  Flash: {flash_match.group(1)}% ({flash_match.group(2)} bytes)[/dim]")
        
        return True
    
    # Build failed - analyze error and try to fix common issues
    console.print("[yellow]⚠️ Initial build failed, analyzing errors...[/yellow]")
    
    retry_needed = False
    
    # Check for missing git module (common with some FreeRTOS libraries)
    if "ModuleNotFoundError: No module named 'git'" in stderr:
        console.print("[yellow]🔧 Installing missing GitPython dependency...[/yellow]")
        if install_python_dependency("GitPython", output_path):
            retry_needed = True
    
    # Check for FreeRTOS library issues
    if "UnknownPackageError" in stderr and "FreeRTOS" in stderr:
        console.print("[yellow]🔧 FreeRTOS library issue detected, attempting to fix...[/yellow]")
        # Our library dependency logic should handle this, but we could add fallback
        
    # Check for common missing dependencies
    missing_deps = []
    if "No module named 'configparser'" in stderr:
        missing_deps.append("configparser")
    if "No module named 'pathlib'" in stderr:
        missing_deps.append("pathlib2")
    
    if missing_deps:
        console.print(f"[yellow]🔧 Installing missing dependencies: {', '.join(missing_deps)}[/yellow]")
        all_installed = True
        for dep in missing_deps:
            if not install_python_dependency(dep, output_path):
                all_installed = False
        
        if all_installed:
            retry_needed = True
    
    # If we made fixes, retry the build
    if retry_needed:
        console.print("[yellow]🔧 Retrying build after installing dependencies...[/yellow]")
        success, stdout, stderr = run_platformio_command(["pio", "run"], output_path)
        if success:
            console.print("[green]✅ Build successful after installing dependencies![/green]")
            
            # Show memory usage on successful retry
            if "RAM:" in stdout and "Flash:" in stdout:
                ram_match = re.search(r'RAM:\s+\[.*?\]\s+([\d.]+)%\s+\(used (\d+) bytes from (\d+) bytes\)', stdout)
                flash_match = re.search(r'Flash:\s+\[.*?\]\s+([\d.]+)%\s+\(used (\d+) bytes from (\d+) bytes\)', stdout)
                
                if ram_match and flash_match:
                    console.print("[dim]📊 Memory Usage:[/dim]")
                    console.print(f"[dim]  RAM:   {ram_match.group(1)}% ({ram_match.group(2)} bytes)[/dim]")
                    console.print(f"[dim]  Flash: {flash_match.group(1)}% ({flash_match.group(2)} bytes)[/dim]")
            
            return True
    
    # Build still failing - show detailed error info and suggestions
    console.print("[red]❌ Build verification failed[/red]")
    console.print("[yellow]Build output (last 15 lines):[/yellow]")
    if stderr:
        error_lines = stderr.strip().split('\n')
        for line in error_lines[-15:]:
            console.print(f"  [dim]{line}[/dim]")
    
    # Provide specific suggestions based on error content
    console.print("\n[yellow]💡 Troubleshooting suggestions:[/yellow]")
    
    if "FreeRTOS" in stderr.lower():
        console.print("  [yellow]🔧 FreeRTOS build issues:[/yellow]")
        console.print("    • Try: --no-freertos (use framework FreeRTOS)")
        console.print("    • Try: --disable-freertos (disable completely)")
        console.print("    • Check FreeRTOSConfig.h compatibility")
    
    if "hal" in stderr.lower() or "driver" in stderr.lower():
        console.print("  [yellow]🔧 HAL driver issues:[/yellow]")
        console.print("    • Check stm32l4xx_hal_conf.h configuration")
        console.print("    • Verify MCU family detection is correct")
    
    if "undefined reference" in stderr.lower():
        console.print("  [yellow]🔧 Linking issues:[/yellow]")
        console.print("    • Check for missing function implementations")
        console.print("    • Verify all required source files are included")
    
    if "multiple definition" in stderr.lower():
        console.print("  [yellow]🔧 Multiple definition errors:[/yellow]")
        console.print("    • Check for duplicate source files")
        console.print("    • May need to exclude conflicting files")
    
    return False
