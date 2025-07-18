"""
Project analyzer for STM32CubeMX projects.
"""

import re
from pathlib import Path
from typing import Dict, List

from rich.console import Console

from ..constants import MCU_FAMILIES
from ..exceptions import ProjectAnalysisError

console = Console()


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
            raise ProjectAnalysisError(f"No .ioc file found in {self.project_path}")
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
        raise ProjectAnalysisError(f"Unknown MCU family for {mcu_target}")
    
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
