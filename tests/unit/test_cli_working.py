"""
Working unit tests for CLI generate_board command - Tests that actually work.
"""
import pytest
from typer.testing import CliRunner
from pathlib import Path

from stm32bridge.main import app


class TestCLIWorking:
    """Working tests for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_app_exists(self):
        """
        GIVEN: The main CLI app
        WHEN: Importing the app
        THEN: Should exist and be a Typer instance
        """
        assert app is not None
        assert hasattr(app, 'command')

    def test_generate_board_command_exists(self):
        """
        GIVEN: The CLI app
        WHEN: Running the generate-board command with help
        THEN: Should show help without errors
        """
        result = self.runner.invoke(app, ["generate-board", "--help"])
        assert result.exit_code == 0
        assert "Generate custom PlatformIO board file" in result.stdout

    def test_cli_missing_required_name_argument(self):
        """
        GIVEN: The generate-board command
        WHEN: Running without required name argument
        THEN: Should exit with error code
        """
        result = self.runner.invoke(app, ["generate-board"])
        assert result.exit_code != 0

    def test_cli_help_command(self):
        """
        GIVEN: The main CLI app
        WHEN: Running with --help
        THEN: Should show main help message
        """
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "stm32bridge" in result.stdout.lower()

    def test_list_boards_command_exists(self):
        """
        GIVEN: The CLI app
        WHEN: Running the list-boards command with help
        THEN: Should show help without errors
        """
        result = self.runner.invoke(app, ["list-boards", "--help"])
        assert result.exit_code == 0
