"""
Simplified working CLI integration tests.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from stm32bridge.main import app
from stm32bridge.utils.mcu_scraper import MCUSpecs


class TestCLIIntegration:
    """Working CLI integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help_command(self):
        """
        GIVEN: User needs help with CLI usage
        WHEN: Running help command
        THEN: Should display help information successfully
        """
        result = self.runner.invoke(app, ['--help'])
        
        assert result.exit_code == 0
        assert "stm32bridge" in result.stdout.lower()

    def test_generate_board_help(self):
        """
        GIVEN: User needs help with generate-board command
        WHEN: Running generate-board help
        THEN: Should display command-specific help
        """
        result = self.runner.invoke(app, ['generate-board', '--help'])
        
        assert result.exit_code == 0
        assert "Generate custom PlatformIO board file" in result.stdout

    def test_list_boards_command(self):
        """
        GIVEN: CLI app with list-boards command
        WHEN: Running list-boards command
        THEN: Should list available boards
        """
        result = self.runner.invoke(app, ['list-boards'])
        assert result.exit_code == 0

    @patch('stm32bridge.cli.generate_board.STM32Scraper')
    def test_generate_board_with_mock_url(self, mock_scraper_class, sample_mcu_specs, temp_dir):
        """
        GIVEN: Valid URL and mock scraper
        WHEN: Running generate-board with URL source
        THEN: Should successfully create board file
        """
        # Setup mock
        mock_scraper = Mock()
        mock_scraper.scrape_from_url.return_value = sample_mcu_specs
        mock_scraper_class.return_value = mock_scraper
        
        result = self.runner.invoke(app, [
            'generate-board',
            'test_board',
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KCU6',
            '--output', str(temp_dir)
        ])
        
        # Should succeed in generating board
        assert result.exit_code == 0
        
        # Check if board file was created
        board_file = temp_dir / "test_board.json"
        assert board_file.exists()
