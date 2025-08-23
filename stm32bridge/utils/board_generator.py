"""
PlatformIO board file generator for STM32 microcontrollers.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from ..utils.mcu_scraper import MCUSpecs
from rich.console import Console

console = Console()


class BoardFileGenerator:
    """Generate PlatformIO board files from MCU specifications."""
    
    def __init__(self):
        self.templates = {
            'cortex-m0': 'cortex-m0',
            'cortex-m0plus': 'cortex-m0plus',
            'cortex-m3': 'cortex-m3',
            'cortex-m4': 'cortex-m4',
            'cortex-m7': 'cortex-m7'
        }
    
    def generate_board_file(self, specs: MCUSpecs, board_name: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate a PlatformIO board configuration from MCU specs.
        
        Args:
            specs: MCU specifications
            board_name: Name for the board configuration
            output_path: Optional path to save the board file
            
        Returns:
            Board configuration dictionary
        """
        console.print(f"[blue]Generating board file for {specs.part_number}...[/blue]")
        
        # Generate board configuration
        board_config = self._create_board_config(specs, board_name)
        
        # Save to file if output path provided
        if output_path:
            self._save_board_file(board_config, board_name, output_path)
        
        console.print(f"[green]✅ Board file generated for {board_name}[/green]")
        return board_config
    
    def _create_board_config(self, specs: MCUSpecs, board_name: str) -> Dict[str, Any]:
        """Create the board configuration dictionary."""
        
        # Apply part-specific corrections
        corrected_specs = self._apply_part_specific_corrections(specs)
        
        # Base configuration
        config = {
            "build": {
                "core": "stm32",
                "cpu": self._map_core_to_cpu(corrected_specs.core),
                "extra_flags": self._generate_build_flags(corrected_specs),
                "f_cpu": str(corrected_specs.max_frequency) + "L",
                "hwids": [
                    ["0x0483", "0x374B"]  # Default STM32 VID/PID
                ],
                "mcu": corrected_specs.part_number.lower(),
                "product_line": self._get_product_line(corrected_specs.part_number),
                "variant": self._get_variant_name(corrected_specs.part_number)
            },
            "debug": {
                "jlink_device": self._get_jlink_device(corrected_specs.part_number),
                "openocd_target": self._get_openocd_target(corrected_specs.family),
                "svd_path": f"{corrected_specs.part_number}.svd"
            },
            "frameworks": ["stm32cube", "arduino"],
            "name": f"{corrected_specs.part_number} ({corrected_specs.flash_size_kb}KB flash, {corrected_specs.ram_size_kb}KB RAM)",
            "upload": {
                "maximum_ram_size": corrected_specs.ram_size_kb * 1024,
                "maximum_size": corrected_specs.flash_size_kb * 1024,
                "protocol": "stlink",
                "protocols": ["stlink", "jlink", "blackmagic", "mbed"]
            },
            "url": "https://www.st.com/en/microcontrollers-microprocessors.html",
            "vendor": "ST"
        }
        
        # Add connectivity features if available
        if corrected_specs.peripherals.get('USB', 0) > 0:
            config["connectivity"] = config.get("connectivity", [])
            config["connectivity"].append("usb")
        
        if corrected_specs.peripherals.get('CAN', 0) > 0:
            config["connectivity"] = config.get("connectivity", [])
            config["connectivity"].append("can")
        
        # Add peripheral information as metadata
        if corrected_specs.peripherals:
            config["build"]["peripherals"] = corrected_specs.peripherals
        
        if corrected_specs.features:
            config["build"]["features"] = corrected_specs.features
        
        return config
    
    def _apply_part_specific_corrections(self, specs: MCUSpecs) -> MCUSpecs:
        """Apply known corrections for specific STM32 parts."""
        part_number = specs.part_number.upper()
        
        # Create a copy with potential corrections
        corrected_specs = specs
        
        # STM32L432KCU6 specific corrections
        if part_number == "STM32L432KCU6":
            console.print("[yellow]⚠️  Applying STM32L432KCU6-specific corrections[/yellow]")
            
            # Correct flash size: KCU6 variant has 256KB
            # The 'C' in KCU6 indicates 256KB flash
            if specs.flash_size_kb != 256:
                console.print(f"[yellow]  • Correcting flash size: {specs.flash_size_kb}KB → 256KB[/yellow]")
                corrected_specs = MCUSpecs(
                    part_number=specs.part_number,
                    family=specs.family,
                    core=specs.core,
                    max_frequency=specs.max_frequency,
                    flash_size_kb=256,  # Corrected
                    ram_size_kb=specs.ram_size_kb,
                    package=specs.package,
                    pin_count=specs.pin_count,
                    operating_voltage_min=specs.operating_voltage_min,
                    operating_voltage_max=specs.operating_voltage_max,
                    temperature_min=specs.temperature_min,
                    temperature_max=specs.temperature_max,
                    peripherals=specs.peripherals,
                    features=specs.features
                )
            
            # Ensure RAM is correct (64KB for L432xx)
            if corrected_specs.ram_size_kb != 64:
                console.print(f"[yellow]  • Correcting RAM size: {corrected_specs.ram_size_kb}KB → 64KB[/yellow]")
                corrected_specs = MCUSpecs(
                    part_number=corrected_specs.part_number,
                    family=corrected_specs.family,
                    core=corrected_specs.core,
                    max_frequency=corrected_specs.max_frequency,
                    flash_size_kb=corrected_specs.flash_size_kb,
                    ram_size_kb=64,  # Corrected
                    package=corrected_specs.package,
                    pin_count=corrected_specs.pin_count,
                    operating_voltage_min=corrected_specs.operating_voltage_min,
                    operating_voltage_max=corrected_specs.operating_voltage_max,
                    temperature_min=corrected_specs.temperature_min,
                    temperature_max=corrected_specs.temperature_max,
                    peripherals=corrected_specs.peripherals,
                    features=corrected_specs.features
                )
            
            # Ensure max frequency is correct (80MHz for L432xx)
            if corrected_specs.max_frequency != "80000000":
                console.print(f"[yellow]  • Correcting max frequency: {corrected_specs.max_frequency}Hz → 80000000Hz[/yellow]")
                corrected_specs = MCUSpecs(
                    part_number=corrected_specs.part_number,
                    family=corrected_specs.family,
                    core=corrected_specs.core,
                    max_frequency="80000000",  # Corrected
                    flash_size_kb=corrected_specs.flash_size_kb,
                    ram_size_kb=corrected_specs.ram_size_kb,
                    package=corrected_specs.package,
                    pin_count=corrected_specs.pin_count,
                    operating_voltage_min=corrected_specs.operating_voltage_min,
                    operating_voltage_max=corrected_specs.operating_voltage_max,
                    temperature_min=corrected_specs.temperature_min,
                    temperature_max=corrected_specs.temperature_max,
                    peripherals=corrected_specs.peripherals,
                    features=corrected_specs.features
                )
        
        # STM32L432KC specific corrections (different flash size)
        elif part_number == "STM32L432KC":
            if specs.flash_size_kb != 256:
                console.print(f"[yellow]  • Correcting flash size for KC variant: {specs.flash_size_kb}KB → 256KB[/yellow]")
                corrected_specs = MCUSpecs(
                    part_number=specs.part_number,
                    family=specs.family,
                    core=specs.core,
                    max_frequency=specs.max_frequency,
                    flash_size_kb=256,  # Corrected
                    ram_size_kb=specs.ram_size_kb,
                    package=specs.package,
                    pin_count=specs.pin_count,
                    operating_voltage_min=specs.operating_voltage_min,
                    operating_voltage_max=specs.operating_voltage_max,
                    temperature_min=specs.temperature_min,
                    temperature_max=specs.temperature_max,
                    peripherals=specs.peripherals,
                    features=specs.features
                )
        
        # STM32L432KB specific corrections
        elif part_number == "STM32L432KB":
            if specs.flash_size_kb != 128:
                console.print(f"[yellow]  • Correcting flash size for KB variant: {specs.flash_size_kb}KB → 128KB[/yellow]")
                corrected_specs = MCUSpecs(
                    part_number=specs.part_number,
                    family=specs.family,
                    core=specs.core,
                    max_frequency=specs.max_frequency,
                    flash_size_kb=128,  # Corrected
                    ram_size_kb=specs.ram_size_kb,
                    package=specs.package,
                    pin_count=specs.pin_count,
                    operating_voltage_min=specs.operating_voltage_min,
                    operating_voltage_max=specs.operating_voltage_max,
                    temperature_min=specs.temperature_min,
                    temperature_max=specs.temperature_max,
                    peripherals=specs.peripherals,
                    features=specs.features
                )
        
        return corrected_specs
    
    def _map_core_to_cpu(self, core: str) -> str:
        """Map ARM core to PlatformIO CPU designation."""
        core_mapping = {
            'cortex-m0': 'cortex-m0',
            'cortex-m0plus': 'cortex-m0plus',
            'cortex-m3': 'cortex-m3',
            'cortex-m4': 'cortex-m4',
            'cortex-m7': 'cortex-m7'
        }
        return core_mapping.get(core.lower(), 'cortex-m4')
    
    def _generate_build_flags(self, specs: MCUSpecs) -> str:
        """Generate build flags based on MCU specifications."""
        flags = []
        
        # Add MCU definition
        mcu_define = specs.part_number.upper()
        flags.append(f"-D{mcu_define}")
        
        # Add family-specific flags
        family = specs.family.upper()
        if family.startswith('STM32'):
            flags.append(f"-D{family}")
        
        # Add HSE crystal frequency with critical 'U' suffix for C preprocessor
        # This is CRITICAL for proper HAL clock configuration
        hse_value = self._get_hse_value_for_part(specs.part_number)
        flags.append(f"-DHSE_VALUE={hse_value}U")
        
        # Add HAL driver flag
        flags.append("-DUSE_HAL_DRIVER")
        
        # Add FPU flags for Cortex-M4/M7 with FPU
        if specs.core.lower() in ['cortex-m4', 'cortex-m7'] and ('fpu' in specs.features or 'FPU' in specs.features):
            flags.extend([
                "-mfpu=fpv4-sp-d16",
                "-mfloat-abi=hard"
            ])
        
        return ' '.join(flags)
    
    def _get_hse_value_for_part(self, part_number: str) -> str:
        """Get the HSE crystal frequency for specific parts."""
        part_upper = part_number.upper()
        
        # Most STM32 development boards use 8MHz crystal
        # This can be overridden for specific known boards
        if part_upper.startswith('STM32L432'):
            return "8000000"  # 8MHz HSE for L432 series
        elif part_upper.startswith('STM32F4'):
            return "25000000"  # 25MHz HSE common for F4 series
        elif part_upper.startswith('STM32H7'):
            return "25000000"  # 25MHz HSE common for H7 series
        else:
            return "8000000"   # Default 8MHz
    
    def _get_jlink_device(self, part_number: str) -> str:
        """Get the appropriate J-Link device name for the part."""
        part_upper = part_number.upper()
        
        # For STM32L432KCU6, use the closest match
        if part_upper == "STM32L432KCU6":
            return "STM32L432KC"  # Closest J-Link supported variant
        elif part_upper.startswith('STM32L432'):
            return "STM32L432KC"  # Generic L432 J-Link device
        else:
            # For other parts, return the part number itself
            return part_number
    
    def _get_product_line(self, part_number: str) -> str:
        """Extract product line from part number."""
        # Extract series from part number (e.g., STM32L432KC -> STM32L432xx)
        import re
        match = re.search(r'(STM32[A-Z]\d+)', part_number.upper())
        if match:
            return f"{match.group(1)}xx"
        return f"{part_number.upper()}xx"
    
    def _get_variant_name(self, part_number: str) -> str:
        """Get variant name for Arduino core."""
        # Most STM32 variants follow this pattern
        return f"{part_number.upper()}"
    
    def _get_openocd_target(self, family: str) -> str:
        """Get OpenOCD target configuration."""
        family_map = {
            'STM32F0': 'stm32f0x',
            'STM32F1': 'stm32f1x',
            'STM32F2': 'stm32f2x',
            'STM32F3': 'stm32f3x',
            'STM32F4': 'stm32f4x',
            'STM32F7': 'stm32f7x',
            'STM32G0': 'stm32g0x',
            'STM32G4': 'stm32g4x',
            'STM32H7': 'stm32h7x',
            'STM32L0': 'stm32l0x',
            'STM32L1': 'stm32l1x',
            'STM32L4': 'stm32l4x',
            'STM32L5': 'stm32l5x',
            'STM32WB': 'stm32wbx',
            'STM32WL': 'stm32wlx',
        }
        
        return family_map.get(family, 'stm32f4x')
    
    def _save_board_file(self, config: Dict[str, Any], board_name: str, output_path: Path):
        """Save board configuration to JSON file."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        board_file = output_path / f"{board_name}.json"
        
        with open(board_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]Board file saved to: {board_file}[/green]")
    
    def create_boards_dir_structure(self, platformio_project_path: Path, board_name: str, config: Dict[str, Any]):
        """
        Create the boards directory structure in a PlatformIO project.
        
        Args:
            platformio_project_path: Path to the PlatformIO project
            board_name: Name of the custom board
            config: Board configuration dictionary
        """
        boards_dir = platformio_project_path / "boards"
        boards_dir.mkdir(exist_ok=True)
        
        board_file = boards_dir / f"{board_name}.json"
        
        with open(board_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✅ Custom board added to project: boards/{board_name}.json[/green]")
        
        # Update platformio.ini to use the custom board
        self._update_platformio_ini(platformio_project_path, board_name)
    
    def _update_platformio_ini(self, project_path: Path, board_name: str):
        """Update platformio.ini to reference the custom board."""
        ini_file = project_path / "platformio.ini"
        
        if ini_file.exists():
            with open(ini_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for existing board setting and replace it
            import re
            if re.search(r'^board\s*=', content, re.MULTILINE):
                content = re.sub(r'^board\s*=.*$', f'board = {board_name}', content, flags=re.MULTILINE)
            else:
                # Add board setting to [env] section
                if '[env]' in content:
                    content = content.replace('[env]', f'[env]\nboard = {board_name}')
                else:
                    content += f'\n[env]\nboard = {board_name}\n'
            
            with open(ini_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            console.print(f"[green]✅ Updated platformio.ini to use board: {board_name}[/green]")


def create_board_from_url(url: str, board_name: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to create a board file from a URL.
    
    Args:
        url: STM32 product page URL
        board_name: Name for the board configuration
        output_path: Optional path to save the board file
        
    Returns:
        Board configuration dictionary
    """
    from .mcu_scraper import STM32Scraper
    
    scraper = STM32Scraper()
    specs = scraper.scrape_from_url(url)
    
    if not specs:
        raise ValueError(f"Could not extract MCU specifications from URL: {url}")
    
    generator = BoardFileGenerator()
    return generator.generate_board_file(specs, board_name, output_path)
