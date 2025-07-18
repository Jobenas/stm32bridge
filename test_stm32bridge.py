#!/usr/bin/env python3
"""
Simple test script to demonstrate STM32Bridge functionality
"""

from stm32bridge import ProjectAnalyzer, PlatformIOProjectGenerator, FileMigrator
from stm32bridge.exceptions import STM32MigrationError
from pathlib import Path
import sys
import argparse

def test_basic_functionality(project_path=None):
    """Test basic functionality of the STM32Bridge modules"""
    print("Testing STM32Bridge basic functionality...")
    
    # Use provided path or try to find a test project
    if project_path:
        source_path = Path(project_path)
    else:
        # Look for common STM32CubeMX project patterns
        possible_paths = [
            Path.cwd() / "example_project",
            Path.cwd() / "test_project", 
            Path.cwd().parent / "test_project",
            Path.cwd().parent / "example_project"
        ]
        
        source_path = None
        for path in possible_paths:
            if path.exists() and any(path.glob("*.ioc")):
                source_path = path
                break
    
    if not source_path or not source_path.exists():
        print("❌ No STM32CubeMX project found.")
        print("Usage: python test_stm32bridge.py [path_to_stm32_project]")
        print("Or create a test project in one of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return False
    
    # Test project analysis
    try:
        analyzer = ProjectAnalyzer(source_path)
        print(f"✅ ProjectAnalyzer created successfully for: {source_path}")
        
        config = analyzer.extract_mcu_info()
        print(f"✅ Project analysis completed - detected MCU: {config.get('mcu_target', 'Unknown')}")
        
        # Test basic generator creation (without actually generating)
        generator = PlatformIOProjectGenerator(config, "test_board")
        print("✅ PlatformIOProjectGenerator created successfully")
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test STM32Bridge functionality")
    parser.add_argument("project_path", nargs="?", help="Path to STM32CubeMX project directory")
    args = parser.parse_args()
    
    success = test_basic_functionality(args.project_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
