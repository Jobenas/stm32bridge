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
```

### Using Custom Board Files

When you have a custom board JSON file (e.g., generated with `stm32bridge generate-board`), you can use it directly during migration:

```bash
# Generate a custom board first
stm32bridge generate-board my_custom_board --source "https://mouser.com/..."

# Use the custom board during migration
stm32bridge migrate my_cubemx_project my_pio_project --board my_custom_board --board-file ./my_custom_board.json
```

The `--board-file` parameter will automatically:
- Copy the JSON file to the correct `boards/` directory in your PlatformIO project
- Update the `platformio.ini` to use your custom board
- No manual file copying required!
