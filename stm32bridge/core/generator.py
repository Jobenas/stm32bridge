"""
PlatformIO project generator.
"""

from pathlib import Path
from typing import Dict

from rich.console import Console

from ..constants import MCU_FAMILIES
from ..exceptions import STM32MigrationError

console = Console()


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
