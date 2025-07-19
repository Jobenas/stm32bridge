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
        
        # Base configuration
        config = {
            "build": {
                "core": "stm32",
                "cpu": self._map_core_to_cpu(specs.core),
                "extra_flags": self._generate_build_flags(specs),
                "f_cpu": specs.max_frequency,
                "hwids": [
                    ["0x0483", "0x374B"]  # Default STM32 VID/PID
                ],
                "mcu": specs.part_number.lower(),
                "product_line": self._get_product_line(specs.part_number),
                "variant": self._get_variant_name(specs.part_number)
            },
            "debug": {
                "jlink_device": specs.part_number,
                "openocd_target": self._get_openocd_target(specs.family),
                "svd_path": f"{specs.part_number}.svd"
            },
            "frameworks": ["arduino", "stm32cube"],
            "name": f"{specs.part_number} ({specs.flash_size_kb}KB flash, {specs.ram_size_kb}KB RAM)",
            "upload": {
                "maximum_ram_size": specs.ram_size_kb * 1024,
                "maximum_size": specs.flash_size_kb * 1024,
                "protocol": "stlink",
                "protocols": ["jlink", "stlink", "blackmagic", "mbed"]
            },
            "url": "https://www.st.com/en/microcontrollers-microprocessors.html",
            "vendor": "ST"
        }
        
        # Add connectivity features if available
        if specs.peripherals.get('USB', 0) > 0:
            config["connectivity"] = config.get("connectivity", [])
            config["connectivity"].append("usb")
        
        if specs.peripherals.get('CAN', 0) > 0:
            config["connectivity"] = config.get("connectivity", [])
            config["connectivity"].append("can")
        
        # Add peripheral information as metadata
        if specs.peripherals:
            config["build"]["peripherals"] = specs.peripherals
        
        if specs.features:
            config["build"]["features"] = specs.features
        
        return config
    
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
        
        # Add HSE crystal frequency if available (default 8MHz for most STM32)
        flags.append("-DHSE_VALUE=8000000")
        
        # Add FPU flags for Cortex-M4/M7 with FPU
        if specs.core.lower() in ['cortex-m4', 'cortex-m7'] and 'fpu' in specs.features:
            flags.extend([
                "-mfpu=fpv4-sp-d16",
                "-mfloat-abi=hard"
            ])
        
        return ' '.join(flags)
    
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
