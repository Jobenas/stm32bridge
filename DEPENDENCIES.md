# STM32Bridge Dependencies

This document lists all dependencies used by STM32Bridge and their purposes.

## Core Dependencies

These are required for basic functionality:

- **typer>=0.9.0** - CLI framework for building command-line interfaces
- **rich>=13.0.0** - Rich text formatting and console output
- **requests>=2.28.0** - HTTP library for web scraping MCU data
- **beautifulsoup4>=4.11.0** - HTML parsing for web scraping

## Development Dependencies

### Testing Framework
- **pytest>=7.0.0** - Main testing framework
- **pytest-cov>=4.0.0** - Code coverage reporting
- **pytest-mock>=3.10.0** - Mocking support for tests
- **pytest-asyncio>=0.21.0** - Async testing support

### Test Data & Mocking
- **responses>=0.23.0** - HTTP request mocking for web scraping tests
- **factory-boy>=3.2.0** - Test data factories for generating MCU specifications

### Code Quality
- **black>=22.0** - Code formatting
- **flake8>=4.0** - Linting and style checking
- **mypy>=0.900** - Static type checking

## Optional Dependencies

### Build Tools
- **GitPython>=3.1.0** - Git operations for FreeRTOS library management

### PDF Processing (Optional)
- **PyPDF2>=3.0.0** - PDF parsing for datasheet extraction
- **pdfplumber>=0.7.0** - Advanced PDF text extraction

## Installation Options

### Basic Installation
```bash
pip install stm32bridge
```

### Development Installation
```bash
pip install -e .[dev]
# or
pip install -r requirements-dev.txt
```

### Specific Feature Groups
```bash
pip install -e .[test]    # Testing dependencies
pip install -e .[pdf]     # PDF processing
pip install -e .[build]   # Build tools
```

## Dependency Status

✅ All dependencies are properly specified in:
- `pyproject.toml` (modern Python packaging)
- `setup.py` (legacy compatibility)
- `requirements*.txt` (development convenience)

✅ All tests pass (101/101) confirming dependency compatibility
✅ Package builds successfully with all dependencies included
