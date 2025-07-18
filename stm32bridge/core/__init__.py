"""
Core components for STM32Bridge migration tool.
"""

from .analyzer import ProjectAnalyzer
from .generator import PlatformIOProjectGenerator
from .migrator import FileMigrator

__all__ = [
    "ProjectAnalyzer",
    "PlatformIOProjectGenerator",
    "FileMigrator"
]
