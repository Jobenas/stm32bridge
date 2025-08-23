#!/usr/bin/env python3
"""
Test script to verify STM32Bridge board generation enhancements.
This script demonstrates the improvements made for STM32L432KCU6 and related variants.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

def run_command(cmd: str) -> str:
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e.stderr}")
        return ""

def load_board_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a board JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def test_hse_value_fix(board_config: Dict[str, Any]) -> bool:
    """Test that HSE_VALUE has the critical 'U' suffix."""
    extra_flags = board_config.get('build', {}).get('extra_flags', '')
    
    print("Testing HSE_VALUE configuration...")
    print(f"  Extra flags: {extra_flags}")
    
    # Check for HSE_VALUE with U suffix
    hse_found = False
    has_u_suffix = False
    
    if 'HSE_VALUE=' in extra_flags:
        hse_found = True
        # Extract HSE_VALUE portion
        hse_part = extra_flags.split('HSE_VALUE=')[1].split()[0]
        if hse_part.endswith('U'):
            has_u_suffix = True
            print(f"  ✅ HSE_VALUE found with U suffix: {hse_part}")
        else:
            print(f"  ❌ HSE_VALUE found but missing U suffix: {hse_part}")
    else:
        print("  ❌ HSE_VALUE not found in build flags")
    
    return hse_found and has_u_suffix

def test_memory_configuration(board_config: Dict[str, Any], expected_flash_kb: int, expected_ram_kb: int) -> bool:
    """Test that memory sizes are correct."""
    upload = board_config.get('upload', {})
    max_flash = upload.get('maximum_size', 0)
    max_ram = upload.get('maximum_ram_size', 0)
    
    expected_flash_bytes = expected_flash_kb * 1024
    expected_ram_bytes = expected_ram_kb * 1024
    
    print("Testing memory configuration...")
    print(f"  Flash: {max_flash} bytes (expected: {expected_flash_bytes} bytes)")
    print(f"  RAM: {max_ram} bytes (expected: {expected_ram_bytes} bytes)")
    
    flash_correct = max_flash == expected_flash_bytes
    ram_correct = max_ram == expected_ram_bytes
    
    if flash_correct:
        print(f"  ✅ Flash size correct: {expected_flash_kb}KB")
    else:
        print(f"  ❌ Flash size incorrect: got {max_flash//1024}KB, expected {expected_flash_kb}KB")
    
    if ram_correct:
        print(f"  ✅ RAM size correct: {expected_ram_kb}KB")
    else:
        print(f"  ❌ RAM size incorrect: got {max_ram//1024}KB, expected {expected_ram_kb}KB")
    
    return flash_correct and ram_correct

def test_debug_configuration(board_config: Dict[str, Any]) -> bool:
    """Test that debug configuration is properly set."""
    debug = board_config.get('debug', {})
    openocd_target = debug.get('openocd_target', '')
    jlink_device = debug.get('jlink_device', '')
    
    print("Testing debug configuration...")
    print(f"  OpenOCD target: {openocd_target}")
    print(f"  J-Link device: {jlink_device}")
    
    # For STM32L4 family, should be stm32l4x
    openocd_correct = openocd_target == 'stm32l4x'
    # For L432KCU6, should use closest supported variant
    jlink_correct = jlink_device in ['STM32L432KC', 'STM32L432KCU6']
    
    if openocd_correct:
        print("  ✅ OpenOCD target correct for STM32L4")
    else:
        print(f"  ❌ OpenOCD target incorrect: expected 'stm32l4x', got '{openocd_target}'")
    
    if jlink_correct:
        print("  ✅ J-Link device appropriate for STM32L432")
    else:
        print(f"  ❌ J-Link device may be incorrect: {jlink_device}")
    
    return openocd_correct and jlink_correct

def test_build_flags(board_config: Dict[str, Any]) -> bool:
    """Test that all necessary build flags are present."""
    extra_flags = board_config.get('build', {}).get('extra_flags', '')
    
    print("Testing build flags...")
    print(f"  Extra flags: {extra_flags}")
    
    required_flags = [
        'STM32L432KCU6',  # MCU definition
        'STM32L4',        # Family definition
        'HSE_VALUE=',     # HSE crystal frequency
        'USE_HAL_DRIVER'  # HAL driver flag
    ]
    
    all_present = True
    for flag in required_flags:
        if flag in extra_flags:
            print(f"  ✅ Required flag present: {flag}")
        else:
            print(f"  ❌ Missing required flag: {flag}")
            all_present = False
    
    return all_present

def test_framework_order(board_config: Dict[str, Any]) -> bool:
    """Test that frameworks are in the correct order."""
    frameworks = board_config.get('frameworks', [])
    
    print("Testing framework configuration...")
    print(f"  Frameworks: {frameworks}")
    
    # STM32Cube should come first for professional development
    correct_order = len(frameworks) >= 2 and frameworks[0] == 'stm32cube'
    
    if correct_order:
        print("  ✅ STM32Cube framework listed first (recommended for professional development)")
    else:
        print("  ❌ Framework order could be improved (STM32Cube should be first)")
    
    return correct_order

def generate_and_test_board(board_name: str, source_url: str) -> bool:
    """Generate a board file and test all enhancements."""
    print(f"\n{'='*60}")
    print(f"Testing Enhanced Board Generation: {board_name}")
    print(f"{'='*60}")
    
    # Generate the board file
    print("Generating board file...")
    cmd = f'stm32bridge generate-board {board_name} --source "{source_url}"'
    output = run_command(cmd)
    
    if not output:
        print("❌ Failed to generate board file")
        return False
    
    print("✅ Board file generated successfully")
    
    # Load the generated board file
    board_file = f"{board_name}.json"
    if not Path(board_file).exists():
        print(f"❌ Board file not found: {board_file}")
        return False
    
    board_config = load_board_file(board_file)
    if not board_config:
        print("❌ Failed to load board configuration")
        return False
    
    print(f"\n📋 Board Configuration Summary:")
    print(f"  Name: {board_config.get('name', 'Unknown')}")
    print(f"  MCU: {board_config.get('build', {}).get('mcu', 'Unknown')}")
    print(f"  CPU: {board_config.get('build', {}).get('cpu', 'Unknown')}")
    print(f"  Frequency: {board_config.get('build', {}).get('f_cpu', 'Unknown')}")
    
    # Run all tests
    print(f"\n🧪 Running Enhancement Tests:")
    print("-" * 40)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: HSE_VALUE with U suffix
    if test_hse_value_fix(board_config):
        tests_passed += 1
    
    print()
    
    # Test 2: Memory configuration (256KB flash, 64KB RAM for KCU6)
    if test_memory_configuration(board_config, 256, 64):
        tests_passed += 1
    
    print()
    
    # Test 3: Debug configuration
    if test_debug_configuration(board_config):
        tests_passed += 1
    
    print()
    
    # Test 4: Build flags
    if test_build_flags(board_config):
        tests_passed += 1
    
    print()
    
    # Test 5: Framework order
    if test_framework_order(board_config):
        tests_passed += 1
    
    # Summary
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All enhancement tests PASSED! Board generation is working correctly.")
        return True
    else:
        print("⚠️  Some enhancement tests FAILED. Board generation needs improvement.")
        return False

def compare_with_previous_version():
    """Compare current board generation with expected improvements."""
    print("🔍 Testing STM32Bridge Enhanced Board Generation")
    print("This test verifies that critical fixes for STM32L432KCU6 are working correctly.")
    print("\nKey improvements being tested:")
    print("1. HSE_VALUE with required 'U' suffix for proper HAL clock configuration")
    print("2. Accurate memory sizes (256KB flash, 64KB RAM for KCU6 variant)")
    print("3. Proper debug configuration (OpenOCD stm32l4x, J-Link STM32L432KC)")
    print("4. Complete build flags with all necessary STM32L4 definitions")
    print("5. Optimal framework ordering (STM32Cube first)")
    
    # Test with STM32L432KCU6
    mouser_url = "https://www.mouser.com/ProductDetail/STMicroelectronics/STM32L432KCU6?qs=Kwkm2GFMXRX7vaNKLH9mjw%3D%3D"
    
    success = generate_and_test_board("test_enhanced_l432kcu6", mouser_url)
    
    if success:
        print("\n🎯 CONCLUSION: Enhanced board generation is working correctly!")
        print("The critical fixes for STM32L432KCU6 have been successfully implemented.")
        print("Projects using this board file should now compile and run without issues.")
    else:
        print("\n❌ CONCLUSION: Board generation needs attention.")
        print("Some critical fixes may not be working as expected.")
    
    return success

if __name__ == "__main__":
    print("STM32Bridge Board Generation Enhancement Test")
    print("=" * 50)
    
    # Check if stm32bridge is available
    try:
        result = subprocess.run(['stm32bridge', '--version'], capture_output=True, text=True, check=True)
        print(f"STM32Bridge version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ STM32Bridge not found. Please install it first:")
        print("   pip install -e .")
        sys.exit(1)
    
    success = compare_with_previous_version()
    
    sys.exit(0 if success else 1)
