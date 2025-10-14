# STM32Bridge - STM32CubeMX to PlatformIO Migration Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PlatformIO](https://img.shields.io/badge/PlatformIO-Compatible-orange.svg)](https://platformio.org/)

A comprehensive CLI utility to automate the migration of STM32CubeMX projects to PlatformIO with full FreeRTOS support.

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install stm32bridge
```

### Development Installation
```bash
git clone https://github.com/jobenas/stm32bridge.git
cd stm32bridge
pip install -e .

# For testing and development
pip install -r requirements-dev.txt

# Or install specific dependency groups
pip install -e .[test]     # Testing dependencies
pip install -e .[dev]      # Development tools  
pip install -e .[pdf]      # PDF processing (optional)
pip install -e .[build]    # Build tools
```

### From Local Wheel
```bash
# Build and install from source
git clone https://github.com/jobenas/stm32bridge.git
cd stm32bridge
pip install build
python -m build
pip install dist/stm32bridge-1.0.0-py3-none-any.whl
```

### Prerequisites
- Python 3.8 or higher
- PlatformIO Core (automatically checked and installed if needed)
- Git (for some FreeRTOS library dependencies)

## 🚀 Features

- **Complete Project Migration**: Analyzes STM32CubeMX projects and creates fully configured PlatformIO projects
- **FreeRTOS Support**: Automatic FreeRTOS library integration with CMSIS-OS v2 compatibility
- **Build Verification**: Integrated build testing with automatic dependency resolution
- **Editor Integration**: Open migrated projects directly in your favorite code editor
- **Board Detection**: Automatic MCU and board detection with extensive board mapping
- **Flexible Configuration**: Support for custom boards, FreeRTOS configurations, and build options

## 📁 Project Structure

```
stm32bridge/
├── main.py                    # CLI entry point
├── stm32bridge/
│   ├── __init__.py           # Package initialization
│   ├── constants.py          # MCU families and board mappings
│   ├── exceptions.py         # Custom exceptions
│   ├── core/                 # Core migration logic
│   │   ├── analyzer.py       # STM32CubeMX project analysis
│   │   ├── generator.py      # PlatformIO project generation
│   │   └── migrator.py       # File migration and adaptation
│   ├── utils/                # Utility modules
│   │   ├── build.py          # Build verification and dependency management
│   │   ├── editor.py         # Code editor integration
│   │   ├── platformio.py     # PlatformIO command execution
│   │   └── boards.py         # Board detection utilities
│   └── cli/                  # CLI command implementations
│       ├── migrate.py        # Migration command
│       ├── analyze.py        # Analysis command
│       └── list_boards.py    # Board listing command
└── stm32bridge.py            # Legacy monolithic version (for reference)
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- PlatformIO Core (installed via pip or standalone)

### Install STM32Bridge

```bash
# Clone the repository
git clone <repository-url>
cd stm32bridge

# Install in development mode
pip install -e .

# For development with all dependencies
pip install -r requirements-dev.txt

# Or install specific dependency groups  
pip install -e .[test]     # Testing dependencies
pip install -e .[dev]      # Development tools
pip install -e .[pdf]      # PDF processing (optional)
```

## 📖 Usage

### Basic Migration

```bash
# Migrate a project with automatic board detection
stm32bridge migrate my_stm32_project my_platformio_project

# Specify a specific board
stm32bridge migrate my_stm32_project my_platformio_project --board nucleo_l432kc

# Windows example
stm32bridge migrate C:\Projects\MySTM32Project C:\Projects\MyPlatformIOProject --board nucleo_f401re

# Linux/Mac example  
stm32bridge migrate ~/projects/my_stm32_project ~/projects/my_platformio_project --board disco_f407vg
```

### Advanced Options

```bash
# Migrate with build verification
stm32bridge migrate my_stm32_project my_platformio_project --board nucleo_l432kc --build

# Migrate and open in VS Code
stm32bridge migrate my_stm32_project my_platformio_project --board nucleo_l432kc --open

# Use different editor
stm32bridge migrate my_stm32_project my_platformio_project --board nucleo_l432kc --open --editor code

# Force overwrite existing directory
stm32bridge migrate my_stm32_project my_platformio_project --force
```

### FreeRTOS Options

```bash
# Use framework FreeRTOS instead of external library
stm32bridge migrate my_stm32_project my_platformio_project --no-freertos

# Completely disable FreeRTOS migration
stm32bridge migrate my_stm32_project my_platformio_project --disable-freertos

# Use PlatformIO framework's built-in FreeRTOS
stm32bridge migrate my_stm32_project my_platformio_project --framework-freertos
```

### Analysis and Information

```bash
# Analyze project without migration
stm32bridge analyze my_stm32_project

# List supported boards
stm32bridge list-boards

# Get help
stm32bridge --help
stm32bridge migrate --help
```

## 🔧 Supported Features

### MCU Families
- STM32F0, F1, F2, F3, F4, F7
- STM32G0, G4
- STM32H7
- STM32L0, L1, L4, L5
- STM32U5
- STM32WB

### FreeRTOS Integration
- Automatic FreeRTOS library detection and integration
- CMSIS-OS v2 compatibility layer
- Custom FreeRTOS configuration preservation
- Support for timers, event groups, and other FreeRTOS features

### Build System
- Complete PlatformIO configuration generation
- Automatic dependency resolution
- Build verification with memory usage reporting
- Support for custom build flags and configurations

### Development Tools
- VS Code, VSCodium, Sublime Text, Atom, Vim support
- STLink upload and debug configuration
- Serial monitor setup
- Custom board definitions

## 🎯 Example Workflow

1. **Generate STM32CubeMX Project**: Create your project with Makefile toolchain
2. **Analyze**: `python main.py analyze /path/to/project` to verify compatibility
3. **Migrate**: `python main.py migrate /path/to/project /path/to/output --board nucleo_l432kc --build --open`
4. **Develop**: Your PlatformIO project is ready with full build and debug support!

## 🐛 Troubleshooting

### Common Issues

- **Build Failures**: Use `--build` flag to get detailed error analysis and automatic fixes
- **Missing Dependencies**: Tool automatically installs required Python packages (GitPython, etc.)
- **FreeRTOS Issues**: Try `--no-freertos` or `--framework-freertos` flags
- **Board Detection**: Use `python main.py list-boards` to find the correct board name

### Debug Options

- Use `python main.py analyze` to validate project structure
- Check PlatformIO installation: `pio --version`
- Verify board support: `pio boards | grep <your-mcu>`

## 🤝 Contributing

The codebase is now well-organized and modular:

- **Core Logic**: Add new features in `stm32bridge/core/`
- **Utilities**: Add helper functions in `stm32bridge/utils/`
- **CLI Commands**: Add new commands in `stm32bridge/cli/`
- **Configuration**: Update constants in `stm32bridge/constants.py`

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- PlatformIO team for the excellent embedded development platform
- STMicroelectronics for STM32CubeMX
- FreeRTOS community for real-time OS support
