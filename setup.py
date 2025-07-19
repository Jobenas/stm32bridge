#!/usr/bin/env python3
"""
Setup script for STM32Bridge - STM32CubeMX to PlatformIO Migration Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read version from the package
def get_version():
    """Extract version from __init__.py"""
    import re
    with open("stm32bridge/__init__.py", "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__version__ = [\'"]([^\'"]*)[\'"]', content)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")

def get_author():
    """Extract author from __init__.py"""
    import re
    with open("stm32bridge/__init__.py", "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'__author__ = [\'"]([^\'"]*)[\'"]', content)
        if match:
            return match.group(1)
        return "STM32Bridge Team"

version = get_version()
author = get_author()

setup(
    name="stm32bridge",
    version=version,
    author=author,
    description="STM32CubeMX to PlatformIO Migration Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stm32bridge",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.11.0",
        "pathlib2>=2.3.0; python_version<'3.4'",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
            "mypy>=0.900",
        ],
        "build": [
            "GitPython>=3.1.0",  # For some FreeRTOS libraries
        ],
        "pdf": [
            "PyPDF2>=3.0.0",
            "pdfplumber>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stm32bridge=stm32bridge.main:app",
        ],
    },
    keywords=[
        "stm32", "cubemx", "platformio", "embedded", "migration", 
        "freertos", "arm", "cortex", "microcontroller", "iot"
    ],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/stm32bridge/issues",
        "Source": "https://github.com/yourusername/stm32bridge",
        "Documentation": "https://github.com/yourusername/stm32bridge/blob/main/README.md",
    },
    include_package_data=True,
    zip_safe=False,
)
