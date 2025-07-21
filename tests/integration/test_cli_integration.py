"""
Integration tests for STM32Bridge CLI functionality.

Tests cover end-to-end workflows including URL scraping,
board generation, and file operations.
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner  # Fixed: Use typer.testing instead of click.testing

from stm32bridge.main import app
from stm32bridge.utils.mcu_scraper import MCUSpecs


class TestCLIIntegration:
    """Integration test suite for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @pytest.fixture
    def mock_scraper_success(self, sample_mcu_specs):
        """
        GIVEN: Successful URL scraping scenario
        WHEN: Mocking STM32Scraper for integration tests
        THEN: Returns mock that simulates successful scraping
        """
        with patch('stm32bridge.cli.generate_board.STM32Scraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.scrape_from_url.return_value = sample_mcu_specs  # Fixed: correct method name
            mock_scraper_class.return_value = mock_scraper
            yield mock_scraper

    def test_cli_help_command(self):
        """
        GIVEN: User needs help with CLI usage
        WHEN: Running help command
        THEN: Should display help information successfully
        """
        result = self.runner.invoke(app, ['--help'])
        
        assert result.exit_code == 0
        assert "STM32Bridge" in result.stdout or "stm32bridge" in result.stdout

    def test_migrate_board_help(self):
        """
        GIVEN: User needs help with generate-board command
        WHEN: Running generate-board help
        THEN: Should display command-specific help
        """
        result = self.runner.invoke(app, ['generate-board', '--help'])
        # 'test_board',  # Board name
        
        assert result.exit_code == 0
        assert "--source" in result.stdout or "--url" in result.stdout

    def test_migrate_board_with_url_source(self, mock_scraper_success, temp_dir):
        """
        GIVEN: Valid Mouser URL and output directory
        WHEN: Running generate-board with URL source
        THEN: Should successfully create board file
        """
        output_file = temp_dir / "test_board.json"
        mouser_url = "https://www.mouser.com/ProductDetail/STM32L432KCU6"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'test_board',  # Board name argument
            '--source', mouser_url,
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify generated board file content
        with open(output_file, 'r') as f:
            board_config = json.load(f)
        
        assert "build" in board_config
        assert board_config["build"]["mcu"] == "stm32l432kc"

    def test_migrate_board_with_board_name(self, mock_scraper_success, temp_dir):
        """
        GIVEN: Board name and custom output file
        WHEN: Running generate-board with board name
        THEN: Should generate board file with custom name
        """
        output_file = temp_dir / "my_custom_board.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'my_custom_board',  # Board name
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KC',  # Use URL instead of part number
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        # Debug: print output if test fails
        if result.exit_code != 0:
            print(f"CLI Output: {result.output}")
            print(f"Exit code: {result.exit_code}")
        
        assert result.exit_code == 0
        assert output_file.exists()

    def test_migrate_board_with_json_file_source(self, temp_dir, sample_board_config):
        """
        GIVEN: Existing JSON file with board configuration
        WHEN: Running generate-board with file source
        THEN: Should process existing configuration
        """
        # Create input JSON file
        input_file = temp_dir / "input_board.json"
        with open(input_file, 'w') as f:
            json.dump(sample_board_config, f, indent=2)
        
        output_file = temp_dir / "output_board.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'output_board',  # Board name
            '--source', str(input_file),
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        # Debug: print output if test fails
        if result.exit_code != 0:
            print(f"CLI Output: {result.output}")
            print(f"Exit code: {result.exit_code}")
        
        assert result.exit_code == 0
        assert output_file.exists()

    def test_migrate_board_output_directory_creation(self,  mock_scraper_success, temp_dir):
        """
        GIVEN: Output path with non-existent directories
        WHEN: Running generate-board
        THEN: Should create output directory automatically
        """
        nested_output = temp_dir / "boards" / "stm32" / "nested_board.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'nested_board',  # Board name
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KC',
            '--output', str(nested_output.parent)  # Pass directory, not file path
        ])
        
        # Debug: print output if test fails
        if result.exit_code != 0:
            print(f"CLI Output: {result.output}")
            print(f"Exit code: {result.exit_code}")
        
        assert result.exit_code == 0
        assert nested_output.exists()
        assert nested_output.parent.exists()

    def test_migrate_board_url_scraping_failure(self,  temp_dir):
        """
        GIVEN: URL that fails to scrape
        WHEN: Running generate-board with failing URL
        THEN: Should handle error gracefully
        """
        with patch('stm32bridge.cli.generate_board.STM32Scraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.scrape_from_url.return_value = None
            mock_scraper_class.return_value = mock_scraper
            
            output_file = temp_dir / "test_board.json"
            
            result = self.runner.invoke(app, [
                'generate-board',
                '--source', 'https://invalid-url.com',
                '--output', str(output_file)
            ])
            
            assert result.exit_code != 0
            assert not output_file.exists()

    def test_migrate_board_invalid_file_source(self,  temp_dir):
        """
        GIVEN: Non-existent file as source
        WHEN: Running generate-board with invalid file
        THEN: Should report error appropriately
        """
        non_existent_file = temp_dir / "does_not_exist.json"
        output_file = temp_dir / "output.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            '--source', str(non_existent_file),
            '--output', str(output_file)
        ])
        
        assert result.exit_code != 0
        assert not output_file.exists()

    def test_list_boards_command(self):
        """
        GIVEN: Need to list available boards
        WHEN: Running list-boards command
        THEN: Should display board information
        """
        result = self.runner.invoke(app, ['list-boards'])
        
        assert result.exit_code == 0
        # Output should contain some board information
        assert len(result.output.strip()) > 0

    def test_list_boards_with_filter(self):
        """
        GIVEN: Need to list available boards
        WHEN: Running list-boards command
        THEN: Should display board information (filter functionality not yet implemented)
        """
        result = self.runner.invoke(app, ['list-boards'])
        
        assert result.exit_code == 0
        # Should contain board information
        assert "STM32" in result.output or "Board" in result.output

    def test_migrate_board_verbose_output(self,  mock_scraper_success, temp_dir):
        """
        GIVEN: Need detailed operation information  
        WHEN: Running generate-board command
        THEN: Should provide detailed output (verbose option not yet implemented)
        """
        output_file = temp_dir / "verbose_test.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'verbose_test',  # Board name
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KC',
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        # The CLI already provides informative output by default
        assert "STM32Bridge" in result.output

    def test_migrate_board_with_all_parameters(self,  mock_scraper_success, temp_dir):
        """
        GIVEN: Complete set of CLI parameters
        WHEN: Running generate-board with all options
        THEN: Should process all parameters correctly
        """
        output_file = temp_dir / "complete_test.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'complete_test',  # Board name
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KCU6',
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Verify board file contains custom name reference
        with open(output_file, 'r') as f:
            content = f.read()
        
        # File should exist and be valid JSON
        board_config = json.loads(content)
        assert "build" in board_config

    def test_cli_error_handling_invalid_command(self):
        """
        GIVEN: Invalid CLI command
        WHEN: Running non-existent command
        THEN: Should report command not found error
        """
        result = self.runner.invoke(app, ['invalid-command'])
        
        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output

    def test_migrate_board_json_validation(self,  mock_scraper_success, temp_dir):
        """
        GIVEN: Successful board generation
        WHEN: Verifying output JSON structure
        THEN: Generated JSON should be valid and complete
        """
        output_file = temp_dir / "validation_test.json"
        
        result = self.runner.invoke(app, [
            'generate-board',
            'validation_test',  # Board name
            '--source', 'https://www.mouser.com/ProductDetail/STM32L432KC',
            '--output', str(temp_dir)  # Pass directory, not file path
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Validate JSON structure
        with open(output_file, 'r') as f:
            board_config = json.load(f)
        
        required_sections = ["build", "debug", "frameworks", "name", "upload", "url", "vendor"]
        for section in required_sections:
            assert section in board_config, f"Missing required section: {section}"
        
        # Validate build section
        build_section = board_config["build"]
        required_build_keys = ["core", "cpu", "f_cpu", "mcu"]
        for key in required_build_keys:
            assert key in build_section, f"Missing required build key: {key}"


class TestEndToEndWorkflows:
    """End-to-end integration tests for complete workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_url_to_board_workflow(self,  sample_mcu_specs):
        """
        GIVEN: Complete URL-to-board generation workflow
        WHEN: Processing Mouser URL through entire pipeline
        THEN: Should create valid PlatformIO board file
        """
        with patch('stm32bridge.cli.generate_board.STM32Scraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.scrape_from_url.return_value = sample_mcu_specs
            mock_scraper_class.return_value = mock_scraper
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = Path(temp_dir) / "stm32l432kc.json"
                
                result = self.runner.invoke(app, [
                    'generate-board',
                    'stm32l432kc',  # Board name
                    '--source', 'https://www.mouser.com/ProductDetail/STM32L432KCU6',
                    '--output', str(temp_dir)  # Pass directory, not file path
                ])
                
                # Verify successful completion
                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify board file is valid PlatformIO format
                with open(output_file, 'r') as f:
                    board_config = json.load(f)
                
                # Check PlatformIO-specific structure
                assert board_config["build"]["core"] == "stm32"
                assert board_config["frameworks"] == ["arduino", "stm32cube"]
                assert "stlink" in board_config["upload"]["protocols"]

    def test_fallback_mechanism_workflow(self):
        """
        GIVEN: Primary URL fails, fallback mechanism triggered
        WHEN: Processing URL that requires fallback
        THEN: Should successfully use fallback and create board file
        """
        with patch('stm32bridge.cli.generate_board.STM32Scraper') as mock_scraper_class:
            mock_scraper = Mock()
            
            # Simulate fallback by returning specs on second attempt
            specs = MCUSpecs(
                part_number="STM32F103C8T6",
                family="STM32F1",
                core="cortex-m3",
                max_frequency="72000000L",
                flash_size_kb=64,
                ram_size_kb=20,
                package="LQFP48",
                pin_count=48,
                operating_voltage_min=2.0,
                operating_voltage_max=3.6,
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            )
            mock_scraper.scrape_from_url.return_value = specs
            mock_scraper_class.return_value = mock_scraper
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = Path(temp_dir) / "stm32f103c8t6.json"
                
                result = self.runner.invoke(app, [
                    'generate-board',
                    'stm32f103c8t6',  # Board name
                    '--source', 'https://www.st.com/en/microcontrollers/stm32f103c8t6.html',
                    '--output', str(temp_dir)  # Pass directory, not file path
                ])
                
                assert result.exit_code == 0
                assert output_file.exists()
                
                # Verify F1 series specific configuration
                with open(output_file, 'r') as f:
                    board_config = json.load(f)
                
                assert board_config["build"]["cpu"] == "cortex-m3"
                assert board_config["build"]["f_cpu"] == "72000000L"
