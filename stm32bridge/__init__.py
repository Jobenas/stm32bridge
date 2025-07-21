"""
STM32CubeMX to PlatformIO Migration Tool

A comprehensive CLI utility to automate the migration of STM32CubeMX projects to PlatformIO.
"""

__version__ = "1.2.2"
__author__ = "STM32Bridge Team"
__license__ = "MIT"

from .core.analyzer import ProjectAnalyzer
from .core.generator import PlatformIOProjectGenerator
from .core.migrator import FileMigrator
from .utils.platformio import check_platformio_installed, run_platformio_command
from .utils.editor import open_project_in_editor
from .utils.build import verify_and_build_project

__all__ = [
    "ProjectAnalyzer",
    "PlatformIOProjectGenerator", 
    "FileMigrator",
    "check_platformio_installed",
    "run_platformio_command",
    "open_project_in_editor",
    "verify_and_build_project"
]
