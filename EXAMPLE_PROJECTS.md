# STM32Bridge Example Projects

This document shows how to create simple test projects for STM32Bridge.

## Creating a Test STM32CubeMX Project

To test STM32Bridge without an existing project, you can create a minimal test structure:

### Method 1: Using STM32CubeMX GUI

1. Open STM32CubeMX
2. Create a new project for any STM32 MCU (e.g., STM32L432KC)
3. Enable FreeRTOS if desired
4. Generate code for "Makefile" toolchain
5. Use the generated project with STM32Bridge

### Method 2: Minimal Test Structure

Create a folder with this structure:

```
my_test_project/
├── my_test_project.ioc          # STM32CubeMX configuration file
├── Makefile                     # Build configuration
├── Core/
│   ├── Inc/
│   │   └── main.h
│   └── Src/
│       └── main.c
└── Drivers/
    └── STM32L4xx_HAL_Driver/
        └── (HAL driver files)
```

### Example .ioc Content

Create `my_test_project.ioc`:
```ini
Mcu.Family=STM32L4
Mcu.Name=STM32L432K(B-C)Ux
Mcu.Package=UFQFPN32
Mcu.Pin0=PC14-OSC32_IN
Mcu.Pin1=PC15-OSC32_OUT
Mcu.PinCount=2
ProjectManager.ProjectName=my_test_project
ProjectManager.TargetToolchain=Makefile
```

### Example Makefile Content

Create `Makefile`:
```makefile
TARGET = my_test_project
MCU = -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

C_DEFS = -DUSE_HAL_DRIVER -DSTM32L432xx

# rest of makefile...
```

### Example main.c

Create `Core/Src/main.c`:
```c
#include "main.h"

int main(void) {
    HAL_Init();
    SystemClock_Config();
    
    while (1) {
        // Main loop
    }
}
```

## Testing with STM32Bridge

Once you have a test project:

```bash
# Test analysis
stm32bridge analyze my_test_project

# Test migration with standard board
stm32bridge migrate my_test_project my_platformio_project --board nucleo_l432kc

# Test migration with custom board file
stm32bridge migrate my_test_project my_platformio_project --board custom_l432kcu6 --board-file ./custom_l432kcu6.json

# Test with build verification
stm32bridge migrate my_test_project my_platformio_project --board nucleo_l432kc --build

# Test with build verification and auto-open in VS Code
stm32bridge migrate my_test_project my_platformio_project --board nucleo_l432kc --build --open
```

### Using Custom Board Files

When you have a custom board JSON file (e.g., generated with `stm32bridge generate-board`), you can use it directly during migration:

```bash
# Generate a custom board first
stm32bridge generate-board my_custom_board --source "https://mouser.com/..."

# Use the custom board during migration
stm32bridge migrate my_cubemx_project my_pio_project --board my_custom_board --board-file ./my_custom_board.json

# Complete workflow with build verification and editor opening
stm32bridge migrate my_cubemx_project my_pio_project --board my_custom_board --board-file ./my_custom_board.json --build --open
```

### Enhanced Board Generation for STM32L432KCU6

STM32Bridge now includes specialized handling for STM32L432KCU6 and related variants:

```bash
# Generate enhanced STM32L432KCU6 board file
stm32bridge generate-board agatha_fw_board --source "https://www.mouser.com/ProductDetail/STMicroelectronics/STM32L432KCU6?qs=..."
```

**Key Enhancements:**
- **HSE_VALUE with "U" suffix**: Critical for proper HAL clock configuration
- **Accurate memory sizes**: 256KB flash, 64KB RAM for KCU6 variant
- **Proper debug configuration**: ST-Link and J-Link support
- **Validated build flags**: Includes all necessary STM32L4 definitions

**The generated board file will include:**
```json
{
  "build": {
    "extra_flags": "-DSTM32L432KCU6 -DSTM32L4 -DHSE_VALUE=8000000U -DUSE_HAL_DRIVER",
    "f_cpu": "80000000L"
  },
  "debug": {
    "jlink_device": "STM32L432KC",
    "openocd_target": "stm32l4x"
  }
}
```

The `--board-file` parameter will automatically:
- Copy the JSON file to the correct `boards/` directory in your PlatformIO project
- Update the `platformio.ini` to use your custom board
- No manual file copying required!

The `--open` option will:
- Automatically detect VS Code installation on Windows
- Open the migrated project in your preferred editor
- Works even if VS Code is not in your system PATH
