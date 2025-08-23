#!/usr/bin/env python3
"""
Simple test to verify STM32Bridge board generation enhancements.
This script checks the key improvements for STM32L432KCU6.
"""

import json
from pathlib import Path

def check_board_enhancements(board_file_path):
    """Check if the generated board file has all the enhanced features."""
    print("STM32Bridge Board Enhancement Verification")
    print("=" * 45)
    
    if not Path(board_file_path).exists():
        print(f"❌ Board file not found: {board_file_path}")
        return False
    
    with open(board_file_path, 'r') as f:
        board_config = json.load(f)
    
    print(f"Testing board: {board_config.get('name', 'Unknown')}")
    print("-" * 45)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: HSE_VALUE with U suffix
    extra_flags = board_config.get('build', {}).get('extra_flags', '')
    print("1. HSE_VALUE Configuration:")
    print(f"   Build flags: {extra_flags}")
    
    if 'HSE_VALUE=8000000U' in extra_flags:
        print("   ✅ PASS: HSE_VALUE has required 'U' suffix")
        tests_passed += 1
    else:
        print("   ❌ FAIL: HSE_VALUE missing or incorrect")
    
    # Test 2: Memory sizes (256KB flash, 64KB RAM)
    max_flash = board_config.get('upload', {}).get('maximum_size', 0)
    max_ram = board_config.get('upload', {}).get('maximum_ram_size', 0)
    
    print("\\n2. Memory Configuration:")
    print(f"   Flash: {max_flash} bytes ({max_flash//1024}KB)")
    print(f"   RAM: {max_ram} bytes ({max_ram//1024}KB)")
    
    if max_flash == 262144 and max_ram == 65536:  # 256KB and 64KB
        print("   ✅ PASS: Memory sizes correct for STM32L432KCU6")
        tests_passed += 1
    else:
        print("   ❌ FAIL: Incorrect memory sizes")
    
    # Test 3: Debug configuration
    debug = board_config.get('debug', {})
    openocd_target = debug.get('openocd_target', '')
    jlink_device = debug.get('jlink_device', '')
    
    print("\\n3. Debug Configuration:")
    print(f"   OpenOCD target: {openocd_target}")
    print(f"   J-Link device: {jlink_device}")
    
    if openocd_target == 'stm32l4x' and jlink_device == 'STM32L432KC':
        print("   ✅ PASS: Debug configuration correct")
        tests_passed += 1
    else:
        print("   ❌ FAIL: Debug configuration incorrect")
    
    # Test 4: Required build flags
    required_flags = ['STM32L432KCU6', 'STM32L4', 'USE_HAL_DRIVER']
    print("\\n4. Required Build Flags:")
    
    all_flags_present = True
    for flag in required_flags:
        if flag in extra_flags:
            print(f"   ✅ {flag} present")
        else:
            print(f"   ❌ {flag} missing")
            all_flags_present = False
    
    if all_flags_present:
        tests_passed += 1
    
    # Test 5: Framework order (STM32Cube first)
    frameworks = board_config.get('frameworks', [])
    print("\\n5. Framework Configuration:")
    print(f"   Frameworks: {frameworks}")
    
    if len(frameworks) >= 2 and frameworks[0] == 'stm32cube':
        print("   ✅ PASS: STM32Cube framework listed first")
        tests_passed += 1
    else:
        print("   ❌ FAIL: Framework order could be improved")
    
    # Summary
    print("\\n" + "=" * 45)
    print(f"Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All enhancements VERIFIED! Board generation is working correctly.")
        print("\\nKey improvements confirmed:")
        print("• HSE_VALUE with 'U' suffix for proper HAL compatibility")
        print("• Accurate memory sizes (256KB flash, 64KB RAM)")
        print("• Proper debug configuration for STM32L4 family")
        print("• Complete build flags for successful compilation")
        print("• Optimal framework ordering")
        return True
    else:
        print("⚠️  Some enhancements may need attention.")
        return False

if __name__ == "__main__":
    board_file = "test_simple_l432kcu6.json"
    success = check_board_enhancements(board_file)
    exit(0 if success else 1)
