#!/usr/bin/env python3
"""
Quick script to fix incomplete MCUSpecs constructors in test files.
"""

import re
import sys
from pathlib import Path

def fix_mcu_specs_constructors(file_path):
    """Fix incomplete MCUSpecs constructors by adding missing required fields."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match MCUSpecs constructors that are missing required fields
    # Look for constructors that don't have all 14 required fields
    pattern = r'MCUSpecs\s*\(\s*([^)]+)\s*\)'
    
    def fix_constructor(match):
        args_str = match.group(1)
        
        # Check if this constructor already has all required fields
        required_fields = [
            'part_number', 'family', 'core', 'max_frequency', 
            'flash_size_kb', 'ram_size_kb', 'package', 'pin_count',
            'operating_voltage_min', 'operating_voltage_max',
            'temperature_min', 'temperature_max', 'peripherals', 'features'
        ]
        
        # Count how many of the required fields are present
        present_fields = []
        for field in required_fields:
            if field in args_str:
                present_fields.append(field)
        
        # If all required fields are present, don't modify
        if len(present_fields) >= 14:
            return match.group(0)
        
        # Add missing fields with default values
        missing_defaults = {
            'package': '"LQFP"',
            'pin_count': '64',
            'operating_voltage_min': '1.8',
            'operating_voltage_max': '3.6',
            'temperature_min': '-40',
            'temperature_max': '85',
            'peripherals': '{}',
            'features': '[]'
        }
        
        # Build the complete constructor
        args_lines = args_str.strip().split('\n')
        
        # Add missing fields
        for field, default in missing_defaults.items():
            if field not in args_str:
                # Add proper indentation
                indent = '            '
                args_lines.append(f'{indent}{field}={default},')
        
        # Remove trailing comma from last line and fix formatting
        if args_lines[-1].endswith(','):
            args_lines[-1] = args_lines[-1][:-1]
        
        new_args = '\n'.join(args_lines)
        return f'MCUSpecs(\n{new_args}\n        )'
    
    # Apply the fixes
    new_content = re.sub(pattern, fix_constructor, content, flags=re.DOTALL)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Fixed MCUSpecs constructors in {file_path}")

if __name__ == "__main__":
    test_files = [
        "tests/unit/test_mcu_specs.py",
        "tests/unit/test_board_generator.py", 
        "tests/unit/test_stm32_scraper.py",
        "tests/integration/test_core_integration.py"
    ]
    
    for file_path in test_files:
        if Path(file_path).exists():
            fix_mcu_specs_constructors(file_path)
        else:
            print(f"File not found: {file_path}")
