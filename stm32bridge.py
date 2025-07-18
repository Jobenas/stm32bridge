#!/usr/bin/env python3
"""
STM32CubeMX to PlatformIO Migration Tool

A CLI utility to automate the migration of STM32CubeMX projects to PlatformIO.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

app = typer.Typer(
    name="stm32bridge",
    help="Migrate STM32CubeMX projects to PlatformIO",
    add_completion=False,
)

console = Console()

# MCU family mappings
MCU_FAMILIES = {
    "STM32F0": {"hal_driver": "STM32F0xx_HAL_Driver", "cmsis": "STM32F0xx", "cortex": "cortex-m0"},
    "STM32F1": {"hal_driver": "STM32F1xx_HAL_Driver", "cmsis": "STM32F1xx", "cortex": "cortex-m3"},
    "STM32F2": {"hal_driver": "STM32F2xx_HAL_Driver", "cmsis": "STM32F2xx", "cortex": "cortex-m3"},
    "STM32F3": {"hal_driver": "STM32F3xx_HAL_Driver", "cmsis": "STM32F3xx", "cortex": "cortex-m4"},
    "STM32F4": {"hal_driver": "STM32F4xx_HAL_Driver", "cmsis": "STM32F4xx", "cortex": "cortex-m4"},
    "STM32F7": {"hal_driver": "STM32F7xx_HAL_Driver", "cmsis": "STM32F7xx", "cortex": "cortex-m7"},
    "STM32G0": {"hal_driver": "STM32G0xx_HAL_Driver", "cmsis": "STM32G0xx", "cortex": "cortex-m0plus"},
    "STM32G4": {"hal_driver": "STM32G4xx_HAL_Driver", "cmsis": "STM32G4xx", "cortex": "cortex-m4"},
    "STM32H7": {"hal_driver": "STM32H7xx_HAL_Driver", "cmsis": "STM32H7xx", "cortex": "cortex-m7"},
    "STM32L0": {"hal_driver": "STM32L0xx_HAL_Driver", "cmsis": "STM32L0xx", "cortex": "cortex-m0plus"},
    "STM32L1": {"hal_driver": "STM32L1xx_HAL_Driver", "cmsis": "STM32L1xx", "cortex": "cortex-m3"},
    "STM32L4": {"hal_driver": "STM32L4xx_HAL_Driver", "cmsis": "STM32L4xx", "cortex": "cortex-m4"},
    "STM32L5": {"hal_driver": "STM32L5xx_HAL_Driver", "cmsis": "STM32L5xx", "cortex": "cortex-m33"},
    "STM32U5": {"hal_driver": "STM32U5xx_HAL_Driver", "cmsis": "STM32U5xx", "cortex": "cortex-m33"},
    "STM32WB": {"hal_driver": "STM32WBxx_HAL_Driver", "cmsis": "STM32WBxx", "cortex": "cortex-m4"},
}

# Common PlatformIO board mappings
BOARD_MAPPINGS = {
    "STM32F401RE": "nucleo_f401re",
    "STM32F103C8": "bluepill_f103c8",
    "STM32F407VG": "disco_f407vg",
    "STM32F429ZI": "nucleo_f429zi",
    "STM32F746ZG": "nucleo_f746zg",
    "STM32L476RG": "nucleo_l476rg",
    "STM32G474RE": "nucleo_g474re",
    "STM32H743ZI": "nucleo_h743zi",
}


class STM32MigrationError(Exception):
    """Custom exception for migration errors."""
    pass


class ProjectAnalyzer:
    """Analyzes STM32CubeMX project to extract configuration."""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.makefile_path = project_path / "Makefile"
        self.ioc_path = None
        self.find_ioc_file()
        
    def find_ioc_file(self):
        """Find the .ioc file in the project."""
        ioc_files = list(self.project_path.glob("*.ioc"))
        if not ioc_files:
            raise STM32MigrationError(f"No .ioc file found in {self.project_path}")
        self.ioc_path = ioc_files[0]
        
    def extract_mcu_info(self) -> Dict[str, str]:
        """Extract MCU information from Makefile and .ioc file."""
        info = {}
        
        # Parse Makefile for build configuration
        if self.makefile_path.exists():
            try:
                makefile_content = self.makefile_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read Makefile: {e}[/yellow]")
                makefile_content = ""
            
            # Extract MCU target
            mcu_match = re.search(r'TARGET\s*=\s*(\w+)', makefile_content)
            if mcu_match:
                info['mcu_target'] = mcu_match.group(1)
            
            # Extract CPU type
            cpu_match = re.search(r'-mcpu=([^\s]+)', makefile_content)
            if cpu_match:
                info['cpu'] = cpu_match.group(1)
                
            # Extract FPU settings
            fpu_match = re.search(r'-mfpu=([^\s]+)', makefile_content)
            if fpu_match:
                info['fpu'] = fpu_match.group(1)
                
            # Extract float ABI
            float_abi_match = re.search(r'-mfloat-abi=([^\s]+)', makefile_content)
            if float_abi_match:
                info['float_abi'] = float_abi_match.group(1)
                
            # Extract defines
            defines = re.findall(r'-D(\w+(?:=\w+)?)', makefile_content)
            info['defines'] = defines
            
        # Parse .ioc file for additional info
        if self.ioc_path and self.ioc_path.exists():
            try:
                ioc_content = self.ioc_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read .ioc file: {e}[/yellow]")
                ioc_content = ""
            
            # Extract MCU family
            mcu_match = re.search(r'Mcu\.Family=(\w+)', ioc_content)
            if mcu_match:
                info['mcu_family'] = mcu_match.group(1)
                
            # Extract specific MCU
            mcu_name_match = re.search(r'Mcu\.Name=(\w+)', ioc_content)
            if mcu_name_match:
                info['mcu_name'] = mcu_name_match.group(1)
                
            # Extract HSE value
            hse_match = re.search(r'RCC\.HSE_VALUE=(\d+)', ioc_content)
            if hse_match:
                info['hse_value'] = hse_match.group(1)
                
            # Extract project name
            project_match = re.search(r'ProjectManager\.ProjectName=([^\r\n]+)', ioc_content)
            if project_match:
                info['project_name'] = project_match.group(1)
            
            # Check for FreeRTOS usage
            freertos_match = re.search(r'FREERTOS\..*=.*true', ioc_content, re.IGNORECASE)
            if freertos_match:
                info['uses_freertos'] = True
            else:
                info['uses_freertos'] = False
        
        # Check for FreeRTOS by looking at main.c includes
        main_c_path = self.project_path / 'Core/Src/main.c'
        if main_c_path.exists():
            try:
                main_content = main_c_path.read_text(encoding='utf-8', errors='ignore')
                if 'cmsis_os.h' in main_content or 'FreeRTOS.h' in main_content:
                    info['uses_freertos'] = True
                    console.print("[yellow]Detected FreeRTOS usage in main.c[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read main.c: {e}[/yellow]")
                
        return info
    
    def detect_mcu_family(self, mcu_target: str) -> str:
        """Detect MCU family from target string."""
        mcu_upper = mcu_target.upper()
        for family in MCU_FAMILIES.keys():
            if mcu_upper.startswith(family):
                return family
        raise STM32MigrationError(f"Unknown MCU family for {mcu_target}")
    
    def validate_project_structure(self) -> bool:
        """Validate that the project has the expected structure."""
        required_dirs = ['Core/Inc', 'Core/Src', 'Drivers']
        required_files = ['Core/Src/main.c']
        
        for dir_path in required_dirs:
            if not (self.project_path / dir_path).exists():
                console.print(f"[red]Missing required directory: {dir_path}[/red]")
                return False
                
        for file_path in required_files:
            if not (self.project_path / file_path).exists():
                console.print(f"[red]Missing required file: {file_path}[/red]")
                return False
                
        return True


class PlatformIOProjectGenerator:
    """Generates PlatformIO project configuration."""
    
    def __init__(self, output_path: Path, project_info: Dict[str, str], no_freertos: bool = False, disable_freertos: bool = False):
        self.output_path = output_path
        self.project_info = project_info
        self.no_freertos = no_freertos
        self.disable_freertos = disable_freertos
        
    def create_project_structure(self):
        """Create the basic PlatformIO project structure."""
        directories = [
            'src', 'include', 'lib', 'test',
            'Core/Inc', 'Core/Src', 'Drivers'
        ]
        
        for dir_name in directories:
            (self.output_path / dir_name).mkdir(parents=True, exist_ok=True)
            
    def generate_platformio_ini(self, board_name: str) -> str:
        """Generate platformio.ini content."""
        mcu_family = self.project_info.get('mcu_family', 'STM32F4')
        family_info = MCU_FAMILIES.get(mcu_family, MCU_FAMILIES['STM32F4'])
        
        # Determine the correct MCU define
        mcu_define = self.project_info.get("mcu_target", "STM32F401xE")
        # If mcu_target is just the project name, try to get it from defines
        if mcu_define == self.project_info.get('project_name'):
            # Look for STM32 define in the defines list
            for define in self.project_info.get('defines', []):
                if define.startswith('STM32') and 'xx' in define:
                    mcu_define = define
                    break
        
        # Build flags
        build_flags = [
            '-D USE_HAL_DRIVER',
            f'-D {mcu_define}',
            f'-D HSE_VALUE={self.project_info.get("hse_value", "8000000")}U',
            '-I include',
            '-I Core/Inc',
            # Use framework HAL drivers (not copied ones)
            # Include path for HAL config file
            f'-I Drivers/{family_info["hal_driver"]}/Inc',
            f'-I Drivers/CMSIS/Device/ST/{family_info["cmsis"]}/Include',
            '-I Drivers/CMSIS/Include',
            '-Wl,-lc -Wl,-lm -Wl,-lnosys',
            '-mthumb',
            f'-mcpu={family_info["cortex"]}'
        ]
        
        # Add FPU flags if available
        if 'fpu' in self.project_info:
            build_flags.append(f'-mfpu={self.project_info["fpu"]}')
            
        if 'float_abi' in self.project_info:
            build_flags.append(f'-mfloat-abi={self.project_info["float_abi"]}')
        
        # Ensure consistent VFP usage across all objects
        if self.project_info.get('fpu') and self.project_info.get('float_abi') == 'hard':
            build_flags.extend([
                '-mfloat-abi=hard',
                '-mfpu=fpv4-sp-d16',
                # Force VFP for all compilation units
                '-Wl,--no-warn-mismatch'
            ])
            
        # Add custom defines
        for define in self.project_info.get('defines', []):
            if define not in ['USE_HAL_DRIVER'] and not define.startswith('STM32'):
                build_flags.append(f'-D {define}')
        
        # Add FreeRTOS-specific configurations
        if self.project_info.get('uses_freertos', False) and not self.disable_freertos:
            if not self.no_freertos:
                # Use external FreeRTOS library
                build_flags.extend([
                    '-D USE_FREERTOS',
                    '-I include',  # For FreeRTOSConfig.h
                    '-D configUSE_CMSIS_RTOS_V2=1'  # Enable CMSIS-RTOS v2 wrapper
                ])
                # Note: The STM32Cube Middleware-FreeRTOS library automatically adds the CMSIS_RTOS_V2 include path
            else:
                # Use framework's built-in FreeRTOS support
                build_flags.extend([
                    '-D USE_FREERTOS',
                    '-D CMSIS_OS_V2'  # Enable CMSIS-RTOS v2 wrapper
                ])
        elif self.disable_freertos:
            # FreeRTOS completely disabled
            console.print("[yellow]FreeRTOS migration disabled - manual setup required[/yellow]")
        
        # Build source filter
        src_filter = [
            '+<*>',
            '+<Core/Src/*>',
            '-<Core/Src/main.c>',  # Exclude main.c since it's in src/
            # Don't include HAL driver sources - use framework versions
            '-<Drivers/STM32L4xx_HAL_Driver/Src/*>',
            # Include any custom middleware
            '+<Drivers/*>',
            '-<Drivers/STM32*HAL_Driver/Src/*>',  # Exclude all HAL driver sources
            '+<Drivers/CMSIS/*>',  # Include CMSIS files
            # Exclude FreeRTOS middleware to avoid conflicts with framework/library
            '-<Middlewares/Third_Party/FreeRTOS/*>',
            '+<Middlewares/*>',  # Include other middleware files
        ]
        
        ini_content = f"""[env:{board_name}]
platform = ststm32
board = {board_name}
framework = stm32cube

; Build configuration
build_flags = 
    {chr(10).join(f'    {flag}' for flag in build_flags)}

; Source file configuration
build_src_filter = 
    {chr(10).join(f'    {filter_item}' for filter_item in src_filter)}

; Libraries
lib_deps = 
    {self._get_library_dependencies()}

; FreeRTOS configuration
{self._get_freertos_config_section()}

; Upload configuration
upload_protocol = stlink
debug_tool = stlink

; Monitor configuration
monitor_speed = 115200

; Debug configuration
debug_init_break = tbreak main
"""
        
        return ini_content
    
    def _get_library_dependencies(self) -> str:
        """Determine required library dependencies based on project configuration."""
        lib_deps = []
        
        # Check for FreeRTOS - use STM32Cube middleware which includes CMSIS-OS2
        if self.project_info.get('uses_freertos', False) and not self.disable_freertos:
            if not self.no_freertos:
                # Use STM32Cube middleware FreeRTOS which includes CMSIS-OS2 wrapper
                lib_deps.append('mincrmatt12/STM32Cube Middleware-FreeRTOS')
            # If using framework FreeRTOS, no additional libraries needed
            
        # Add other common libraries that might be detected in the future
        # USB, Ethernet, etc.
        
        if lib_deps:
            return chr(10).join(f'    {lib}' for lib in lib_deps)
        else:
            return '    ; No additional libraries required'
    
    def _get_freertos_config_section(self) -> str:
        """Generate FreeRTOS-specific configuration section."""
        if self.project_info.get('uses_freertos', False) and not self.disable_freertos:
            if not self.no_freertos:
                # For external FreeRTOS library, specify config location and CMSIS v2
                config_lines = [
                    'custom_freertos_config_location = include/FreeRTOSConfig.h',
                    'custom_freertos_cmsis_impl = CMSIS_RTOS_V2',
                    'custom_freertos_features = timers, event_groups'  # Enable common FreeRTOS features
                ]
                return chr(10).join(config_lines)
            else:
                # For framework FreeRTOS, no additional config needed
                return '; Using framework FreeRTOS - no additional config required'
        else:
            return '; FreeRTOS not used or disabled'
    
    def write_platformio_ini(self, board_name: str):
        """Write platformio.ini file."""
        ini_content = self.generate_platformio_ini(board_name)
        ini_path = self.output_path / 'platformio.ini'
        try:
            ini_path.write_text(ini_content, encoding='utf-8')
            console.print(f"[green]Created platformio.ini[/green]")
        except (OSError, PermissionError) as e:
            console.print(f"[red]Error writing platformio.ini: {e}[/red]")
            raise STM32MigrationError(f"Could not write platformio.ini: {e}")


class FileMigrator:
    """Handles file copying and migration."""
    
    def __init__(self, source_path: Path, dest_path: Path, disable_freertos: bool = False):
        self.source_path = source_path
        self.dest_path = dest_path
        self.disable_freertos = disable_freertos
        
    def copy_directory_tree(self, src_dir: str, dest_dir: str, 
                          exclude_patterns: List[str] = None):
        """Copy directory tree with exclusions."""
        exclude_patterns = exclude_patterns or []
        
        src_path = self.source_path / src_dir
        dest_path = self.dest_path / dest_dir
        
        if not src_path.exists():
            console.print(f"[yellow]Source directory not found: {src_path}[/yellow]")
            return
            
        dest_path.mkdir(parents=True, exist_ok=True)
        
        for item in src_path.rglob('*'):
            if item.is_file():
                # Check exclusions
                relative_path = item.relative_to(src_path)
                if any(pattern in str(relative_path) for pattern in exclude_patterns):
                    continue
                    
                dest_file = dest_path / relative_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(item, dest_file)
                except (OSError, PermissionError) as e:
                    console.print(f"[yellow]Warning: Could not copy {item}: {e}[/yellow]")
                
    def migrate_core_files(self):
        """Copy Core/Src files (except main.c) to src/ directory."""
        core_src = self.source_path / 'Core/Src'
        dest_src = self.dest_path / 'src'
        
        if core_src.exists():
            for src_file in core_src.iterdir():
                if src_file.is_file() and src_file.name.endswith('.c') and src_file.name != 'main.c':
                    # Skip FreeRTOS-related files if disable_freertos is True
                    if self.disable_freertos and ('freertos' in src_file.name.lower() or 'rtos' in src_file.name.lower()):
                        console.print(f"[yellow]Skipping {src_file.name} (--disable-freertos)[/yellow]")
                        continue
                    
                    # Skip syscalls.c to avoid multiple definition errors
                    if src_file.name.lower() in ['syscalls.c', 'sysmem.c']:
                        console.print(f"[yellow]Skipping {src_file.name} (potential conflict with standard library)[/yellow]")
                        continue
                    
                    # For freertos.c, we need to adapt it if using external library
                    if src_file.name.lower() == 'freertos.c' and not self.disable_freertos:
                        self._adapt_freertos_file(src_file, dest_src)
                    else:
                        dest_file = dest_src / src_file.name
                        try:
                            content = src_file.read_text(encoding='utf-8', errors='ignore')
                            dest_file.write_text(content, encoding='utf-8')
                            console.print(f"[green]Copied {src_file.name} to src/[/green]")
                        except (OSError, PermissionError) as e:
                            console.print(f"[red]Error copying {src_file.name}: {e}[/red]")

    def _adapt_freertos_file(self, src_file: Path, dest_src: Path):
        """Adapt freertos.c file for PlatformIO FreeRTOS library."""
        dest_file = dest_src / src_file.name
        try:
            content = src_file.read_text(encoding='utf-8', errors='ignore')
            
            # Replace CubeMX specific includes with PlatformIO compatible ones
            content = content.replace('#include "FreeRTOS.h"', '#include <FreeRTOS.h>')
            content = content.replace('#include "task.h"', '#include <task.h>')
            content = content.replace('#include "main.h"', '#include "main.h"')
            content = content.replace('#include "cmsis_os.h"', '#include <cmsis_os2.h>')
            
            dest_file.write_text(content, encoding='utf-8')
            console.print(f"[green]Copied and adapted {src_file.name} to src/[/green]")
        except (OSError, PermissionError) as e:
            console.print(f"[red]Error copying {src_file.name}: {e}[/red]")

    def migrate_main_file(self):
        """Copy main.c to src/ directory."""
        main_src = self.source_path / 'Core/Src/main.c'
        main_dest = self.dest_path / 'src/main.c'
        
        if main_src.exists():
            # Remove any existing main.cpp
            cpp_main = self.dest_path / 'src/main.cpp'
            if cpp_main.exists():
                cpp_main.unlink()
                
            try:
                # Read and potentially modify main.c for PlatformIO compatibility
                main_content = main_src.read_text(encoding='utf-8', errors='ignore')
                
                # Check if FreeRTOS is used and we need to disable it
                if hasattr(self, 'disable_freertos') and self.disable_freertos and 'cmsis_os.h' in main_content:
                    console.print(f"[yellow]Commenting out FreeRTOS includes in main.c (--disable-freertos)[/yellow]")
                    # Comment out FreeRTOS includes
                    main_content = main_content.replace('#include "cmsis_os.h"', '// #include "cmsis_os.h" // Disabled for PlatformIO migration')
                    # Comment out FreeRTOS function calls (comprehensive)
                    freertos_patterns = [
                        (r'osKernelInitialize\(\);', r'// osKernelInitialize(); // Disabled for PlatformIO migration'),
                        (r'osKernelStart\(\);', r'// osKernelStart(); // Disabled for PlatformIO migration'),
                        (r'MX_FREERTOS_Init\(\);', r'// MX_FREERTOS_Init(); // Disabled for PlatformIO migration'),
                        (r'osThreadNew\(', r'// osThreadNew( // Disabled for PlatformIO migration'),
                        (r'osDelay\(', r'// osDelay( // Disabled for PlatformIO migration')
                    ]
                    for pattern, replacement in freertos_patterns:
                        main_content = re.sub(pattern, replacement, main_content)
                elif 'cmsis_os.h' in main_content:
                    console.print(f"[yellow]Modifying main.c FreeRTOS includes for PlatformIO compatibility[/yellow]")
                    # Replace the CubeMX FreeRTOS include with library include
                    main_content = main_content.replace('#include "cmsis_os.h"', '#include <cmsis_os2.h>')
                    # Add comment explaining the change
                    main_content = main_content.replace('#include <cmsis_os2.h>', 
                        '// Modified for PlatformIO: using FreeRTOS library\n#include <cmsis_os2.h>')
                
                main_dest.write_text(main_content, encoding='utf-8')
                console.print(f"[green]Copied and adapted main.c to src/[/green]")
            except (OSError, PermissionError) as e:
                console.print(f"[red]Error copying main.c: {e}[/red]")
        else:
            console.print(f"[red]main.c not found in {main_src}[/red]")
            
    def migrate_all_files(self):
        """Migrate all necessary files."""
        # Copy Core files (excluding main.c to avoid duplication)
        self.copy_directory_tree('Core/Inc', 'Core/Inc')
        self.copy_directory_tree('Core/Src', 'Core/Src', exclude_patterns=['main.c'])
        
        # Copy only specific driver files to avoid HAL conflicts
        # PlatformIO provides its own HAL drivers, so we only copy user-specific drivers
        self.copy_selective_drivers()
        
        # Copy middleware (FreeRTOS config, etc.)
        self.copy_middleware()
        
        # Handle Core/Src files
        self.migrate_core_files()
        
        # Handle main.c specially
        self.migrate_main_file()
        
        console.print("[green]File migration completed[/green]")
    
    def copy_middleware(self):
        """Copy middleware files like FreeRTOS configuration."""
        middlewares_src = self.source_path / 'Middlewares'
        
        if middlewares_src.exists():
            # Copy FreeRTOS configuration files
            freertos_src = middlewares_src / 'Third_Party/FreeRTOS'
            if freertos_src.exists() and not self.disable_freertos:
                self._copy_freertos_config(freertos_src)
            elif self.disable_freertos:
                console.print("[yellow]Skipping FreeRTOS middleware copy (--disable-freertos)[/yellow]")
            else:
                console.print("[yellow]Skipping FreeRTOS middleware copy - will use PlatformIO's FreeRTOS[/yellow]")
            
            # Copy other middleware
            for item in middlewares_src.iterdir():
                if item.is_dir() and item.name != 'Third_Party':
                    self.copy_directory_tree(f'Middlewares/{item.name}', f'Middlewares/{item.name}')
                    console.print(f"[green]Copied middleware: {item.name}[/green]")
        
        # Also look for FreeRTOSConfig.h in Core/Inc
        if not self.disable_freertos:
            self._copy_freertos_config_from_core()
    
    def _should_copy_freertos_files(self) -> bool:
        """Determine if we should copy FreeRTOS files or let PlatformIO handle it."""
        # For now, let's not copy FreeRTOS middleware to avoid conflicts
        # PlatformIO's framework should handle FreeRTOS
        return False
    
    def _copy_complete_freertos(self, freertos_src: Path):
        """Copy complete FreeRTOS including port files."""
        # This would copy the entire FreeRTOS structure including ports
        # Only use if we're sure about the port compatibility
        freertos_dirs = ['Source']
        for freertos_dir in freertos_dirs:
            config_src = freertos_src / freertos_dir
            if config_src.exists():
                self.copy_directory_tree(f'Middlewares/Third_Party/FreeRTOS/{freertos_dir}', 
                                       f'Middlewares/Third_Party/FreeRTOS/{freertos_dir}')
                console.print(f"[green]Copied complete FreeRTOS: {freertos_dir}[/green]")
    
    def _copy_freertos_config_from_core(self):
        """Copy FreeRTOSConfig.h from Core/Inc if it exists."""
        freertos_config = self.source_path / 'Core/Inc/FreeRTOSConfig.h'
        if freertos_config.exists():
            dest_dir = self.dest_path / 'include'
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Read the original config
                config_content = freertos_config.read_text(encoding='utf-8', errors='ignore')
                
                # Write to include directory for PlatformIO
                dest_file = dest_dir / 'FreeRTOSConfig.h'
                dest_file.write_text(config_content, encoding='utf-8')
                console.print(f"[green]Copied FreeRTOSConfig.h from Core/Inc to include/[/green]")
                
            except (OSError, PermissionError) as e:
                console.print(f"[yellow]Warning: Could not copy FreeRTOSConfig.h: {e}[/yellow]")
        else:
            console.print(f"[yellow]FreeRTOSConfig.h not found in Core/Inc[/yellow]")

    def _copy_freertos_config(self, freertos_src: Path):
        """Copy and adapt FreeRTOSConfig.h for PlatformIO compatibility."""
        freertos_config = freertos_src / 'Source/include/FreeRTOSConfig.h'
        if freertos_config.exists():
            dest_dir = self.dest_path / 'include'
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Read the original config
                config_content = freertos_config.read_text(encoding='utf-8', errors='ignore')
                
                # Add missing defines that PlatformIO's FreeRTOS-Kernel expects
                missing_defines = [
                    '#ifndef configTASK_NOTIFICATION_ARRAY_ENTRIES\n#define configTASK_NOTIFICATION_ARRAY_ENTRIES 1\n#endif\n\n',
                    '#ifndef configUSE_TRACE_FACILITY\n#define configUSE_TRACE_FACILITY 0\n#endif\n\n',
                    '#ifndef configUSE_STATS_FORMATTING_FUNCTIONS\n#define configUSE_STATS_FORMATTING_FUNCTIONS 0\n#endif\n\n',
                    '#ifndef configSUPPORT_STATIC_ALLOCATION\n#define configSUPPORT_STATIC_ALLOCATION 1\n#endif\n\n',
                    '#ifndef configSUPPORT_DYNAMIC_ALLOCATION\n#define configSUPPORT_DYNAMIC_ALLOCATION 1\n#endif\n\n'
                ]
                
                # Find a good place to insert the defines (before the last #endif)
                if '#ifdef __cplusplus' in config_content:
                    insert_pos = config_content.rfind('#ifdef __cplusplus')
                else:
                    insert_pos = config_content.rfind('#endif')
                
                if insert_pos != -1:
                    # Insert the missing defines
                    config_content = (config_content[:insert_pos] + 
                                    ''.join(missing_defines) + 
                                    config_content[insert_pos:])
                else:
                    # If we can't find a good spot, append at the end
                    config_content += '\n' + ''.join(missing_defines)
                
                # Write the adapted config
                dest_file = dest_dir / 'FreeRTOSConfig.h'
                dest_file.write_text(config_content, encoding='utf-8')
                console.print(f"[green]Copied and adapted FreeRTOSConfig.h to include/[/green]")
                
            except (OSError, PermissionError) as e:
                console.print(f"[yellow]Warning: Could not copy FreeRTOSConfig.h: {e}[/yellow]")
        else:
            console.print(f"[yellow]FreeRTOSConfig.h not found, using PlatformIO defaults[/yellow]")
    
    def copy_selective_drivers(self):
        """Copy only necessary driver files, avoiding HAL conflicts."""
        drivers_src = self.source_path / 'Drivers'
        
        if not drivers_src.exists():
            console.print(f"[yellow]Drivers directory not found: {drivers_src}[/yellow]")
            return
        
        # Copy CMSIS files (these are usually safe)
        cmsis_dirs = ['CMSIS/Device', 'CMSIS/Include']
        for cmsis_dir in cmsis_dirs:
            cmsis_src = drivers_src / cmsis_dir
            if cmsis_src.exists():
                cmsis_dest = self.dest_path / 'Drivers' / cmsis_dir
                cmsis_dest.mkdir(parents=True, exist_ok=True)
                self.copy_directory_tree(f'Drivers/{cmsis_dir}', f'Drivers/{cmsis_dir}')
                console.print(f"[green]Copied {cmsis_dir}[/green]")
        
        # Copy user-specific driver files (not standard HAL)
        # Look for custom drivers or middleware
        hal_dir = drivers_src / 'STM32L4xx_HAL_Driver'
        if hal_dir.exists():
            # Only copy the configuration headers, not the source files
            hal_inc_src = hal_dir / 'Inc'
            if hal_inc_src.exists():
                hal_inc_dest = self.dest_path / 'Drivers/STM32L4xx_HAL_Driver/Inc'
                hal_inc_dest.mkdir(parents=True, exist_ok=True)
                # Copy only configuration files, not the HAL driver headers
                config_files = ['stm32l4xx_hal_conf.h', '*_conf.h']
                for pattern in config_files:
                    for config_file in hal_inc_src.glob(pattern):
                        if config_file.is_file():
                            try:
                                dest_file = hal_inc_dest / config_file.name
                                shutil.copy2(config_file, dest_file)
                                console.print(f"[green]Copied HAL config: {config_file.name}[/green]")
                            except (OSError, PermissionError) as e:
                                console.print(f"[yellow]Warning: Could not copy {config_file}: {e}[/yellow]")
        
        # Copy any user-added middleware or custom drivers
        for item in drivers_src.iterdir():
            if item.is_dir() and item.name not in ['STM32L4xx_HAL_Driver', 'CMSIS']:
                # This is likely custom middleware or drivers
                self.copy_directory_tree(f'Drivers/{item.name}', f'Drivers/{item.name}')
                console.print(f"[green]Copied custom driver: {item.name}[/green]")


def detect_board_name(mcu_name: str) -> str:
    """Detect PlatformIO board name from MCU name."""
    mcu_upper = mcu_name.upper()
    
    # Check direct mappings
    for mcu_pattern, board_name in BOARD_MAPPINGS.items():
        if mcu_upper.startswith(mcu_pattern):
            return board_name
    
    # Fallback: ask user or use generic
    console.print(f"[yellow]Could not auto-detect board for MCU: {mcu_name}[/yellow]")
    return "genericSTM32F401RE"  # Generic fallback


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
    
    build_fixed = False
    retry_needed = False
    
    # Check for missing git module (common with some FreeRTOS libraries)
    if "ModuleNotFoundError: No module named 'git'" in stderr:
        console.print("[yellow]🔧 Installing missing GitPython dependency...[/yellow]")
        if install_python_dependency("GitPython", output_path):
            retry_needed = True
            build_fixed = True
    
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
            build_fixed = True
    
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
                    console.print("[dim]� Memory Usage:[/dim]")
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
        console.print("  [yellow]� FreeRTOS build issues:[/yellow]")
        console.print("    • Try: --no-freertos (use framework FreeRTOS)")
        console.print("    • Try: --disable-freertos (disable completely)")
        console.print("    • Check FreeRTOSConfig.h compatibility")
    
    if "hal" in stderr.lower() or "driver" in stderr.lower():
        console.print("  [yellow]� HAL driver issues:[/yellow]")
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


@app.command()
def migrate(
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


@app.command()
def analyze(
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


@app.command()
def list_boards():
    """List common STM32 board mappings for PlatformIO."""
    
    console.print(Panel.fit(
        "[bold blue]Common STM32 Board Mappings[/bold blue]",
        border_style="blue"
    ))
    
    table = Table(title="MCU to PlatformIO Board Mappings")
    table.add_column("MCU", style="cyan")
    table.add_column("PlatformIO Board", style="magenta")
    table.add_column("Description", style="dim")
    
    board_descriptions = {
        "nucleo_f401re": "STM32 Nucleo F401RE",
        "bluepill_f103c8": "STM32F103C8T6 Blue Pill",
        "disco_f407vg": "STM32F407VG Discovery",
        "nucleo_f429zi": "STM32 Nucleo F429ZI",
        "nucleo_f746zg": "STM32 Nucleo F746ZG",
        "nucleo_l476rg": "STM32 Nucleo L476RG",
        "nucleo_g474re": "STM32 Nucleo G474RE",
        "nucleo_h743zi": "STM32 Nucleo H743ZI",
    }
    
    for mcu, board in BOARD_MAPPINGS.items():
        description = board_descriptions.get(board, "")
        table.add_row(mcu, board, description)
    
    console.print(table)
    
    console.print("\n[dim]Note: If your board is not listed, you can:")
    console.print("1. Use a similar board from the same MCU family")
    console.print("2. Check PlatformIO documentation for more boards")
    console.print("3. Use a generic board configuration[/dim]")


if __name__ == "__main__":
    app()