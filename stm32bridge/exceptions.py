"""
Custom exceptions for STM32Bridge.
"""


class STM32MigrationError(Exception):
    """Custom exception for migration errors."""
    pass


class ProjectAnalysisError(STM32MigrationError):
    """Exception raised when project analysis fails."""
    pass


class FileOperationError(STM32MigrationError):
    """Exception raised when file operations fail."""
    pass


class PlatformIOError(STM32MigrationError):
    """Exception raised when PlatformIO operations fail."""
    pass
