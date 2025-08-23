"""
File migration utilities for STM32CubeMX to PlatformIO conversion.
"""

import re
import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..exceptions import FileOperationError

console = Console()


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
        
        # Copy STM32CubeMX .ioc file for peripheral configuration preservation
        self.copy_ioc_file()
        
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
            console.print(f"[yellow]FreeRTOSConfig.h not found, using PlatformIO defaults[/yellow]")

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
    
    def copy_ioc_file(self):
        """Copy the .ioc file to preserve STM32CubeMX configuration."""
        # Look for .ioc files in the source directory
        ioc_files = list(self.source_path.glob('*.ioc'))
        
        if not ioc_files:
            console.print(f"[yellow]No .ioc file found in {self.source_path}[/yellow]")
            return
        
        if len(ioc_files) > 1:
            console.print(f"[yellow]Multiple .ioc files found, copying the first one: {ioc_files[0].name}[/yellow]")
        
        ioc_file = ioc_files[0]
        dest_file = self.dest_path / ioc_file.name
        
        try:
            shutil.copy2(ioc_file, dest_file)
            console.print(f"[green]✅ Copied {ioc_file.name} for peripheral configuration preservation[/green]")
        except (OSError, PermissionError) as e:
            console.print(f"[red]Error copying {ioc_file.name}: {e}[/red]")
            raise FileOperationError(f"Failed to copy .ioc file: {e}")
