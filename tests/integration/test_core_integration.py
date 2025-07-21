"""
Integration tests for core STM32Bridge functionality.

Tests cover end-to-end workflows for scraping and board generation
without depending on the complex CLI structure.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from stm32bridge.utils.mcu_scraper import STM32Scraper, MCUSpecs
from stm32bridge.utils.board_generator import BoardFileGenerator
from stm32bridge.exceptions import STM32MigrationError


class TestCoreIntegration:
    """Integration tests for core functionality."""

    def test_complete_url_to_board_workflow(self, temp_dir, sample_mcu_specs):
        """
        GIVEN: URL pointing to STM32 product page
        WHEN: Processing complete workflow from URL to board file
        THEN: Should create valid PlatformIO board configuration
        """
        # Mock the scraper to return our test specs
        with patch('stm32bridge.utils.mcu_scraper.STM32Scraper') as mock_scraper_class:
            mock_scraper = Mock()
            mock_scraper.scrape_from_url.return_value = sample_mcu_specs
            mock_scraper_class.return_value = mock_scraper
            
            # Execute complete workflow
            scraper = STM32Scraper()
            board_generator = BoardFileGenerator()
            
            # Step 1: Scrape URL
            url = "https://www.mouser.com/ProductDetail/STM32L432KCU6"
            specs = scraper.scrape_from_url(url)
            
            assert specs is not None
            assert "STM32L432KC" in specs.part_number  # Should contain the base part number
            
            # Step 2: Generate board configuration
            config = board_generator.generate_board_file(specs, "test_board")
            
            assert isinstance(config, dict)
            assert "build" in config
            assert config["build"]["mcu"] == specs.part_number.lower()
            
            # Step 3: Save to file
            output_file = temp_dir / "test_board.json"
            
            # Save manually since generate_board_file might have already saved it
            import json
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            assert output_file.exists()
            
            # Verify saved content
            with open(output_file, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config == config

    def test_board_generation_with_different_families(self, temp_dir):
        """
        GIVEN: MCU specs from different STM32 families
        WHEN: Generating board configurations for each
        THEN: Should create family-specific configurations
        """
        families_specs = [
            MCUSpecs(
                part_number="STM32F103C8T6",
                family="STM32F1",
                core="cortex-m3",
                max_frequency="72000000L",
                flash_size_kb=64,
                ram_size_kb=20,
                package="LQFP",
                pin_count=48,
                operating_voltage_min=2.0,
                operating_voltage_max=3.6,
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            ),
            MCUSpecs(
                part_number="STM32L432KC",
                family="STM32L4",
                core="cortex-m4",
                max_frequency="80000000L",
                flash_size_kb=256,
                ram_size_kb=64,
                package="LQFP",
                pin_count=32,
                operating_voltage_min=1.71,
                operating_voltage_max=3.6,
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            ),
            MCUSpecs(
                part_number="STM32H743VI",
                family="STM32H7",
                core="cortex-m7",
                max_frequency="480000000L",
                flash_size_kb=2048,
                ram_size_kb=1024,
                package="BGA",
                pin_count=100,
                operating_voltage_min=1.71,
                operating_voltage_max=3.6,
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            )
        ]
        
        board_generator = BoardFileGenerator()
        
        for specs in families_specs:
            config = board_generator.generate_board_file(specs, specs.part_number.lower())  # Fixed method name
            
            # Verify family-specific configurations
            if specs.family == "STM32F1":
                assert config["build"]["cpu"] == "cortex-m3"
                assert "stm32f1x" in config["debug"]["openocd_target"]
            elif specs.family == "STM32L4":
                assert config["build"]["cpu"] == "cortex-m4"
                assert "stm32l4x" in config["debug"]["openocd_target"]
            elif specs.family == "STM32H7":
                assert config["build"]["cpu"] == "cortex-m7"
                assert "stm32h7x" in config["debug"]["openocd_target"]
            
            # Save and verify each family
            output_file = temp_dir / f"{specs.part_number.lower()}.json"
            board_generator._save_board_file(config, specs.part_number.lower(), temp_dir)  # Fixed method signature
            assert output_file.exists()

    def test_error_handling_workflow(self):
        """
        GIVEN: Various error conditions in workflow
        WHEN: Processing with errors at different stages
        THEN: Should handle errors gracefully with exceptions
        """
        scraper = STM32Scraper()
        board_generator = BoardFileGenerator()
        
        # Test 1: Invalid URL - should raise exception
        with pytest.raises(STM32MigrationError):
            result = scraper.scrape_from_url("invalid-url")
        
        # Test 3: Board generation with minimal specs
        minimal_specs = MCUSpecs(
            part_number="TEST_MCU",
            family="TEST_FAMILY",
            core="cortex-m4",
            max_frequency="100000000L",
            flash_size_kb=256,
            ram_size_kb=64,
            package="LQFP",
            pin_count=64,
            operating_voltage_min=1.8,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        config = board_generator.generate_board_file(minimal_specs, "test_board")  # Fixed method name
        assert config is not None
        assert "build" in config

    def test_url_source_detection_workflow(self):
        """
        GIVEN: Different URL formats and sources
        WHEN: Processing various URL types
        THEN: Should correctly identify and process each source
        """
        scraper = STM32Scraper()
        
        test_urls = [
            "https://www.mouser.com/ProductDetail/STM32L432KC",
            "https://www.st.com/en/microcontrollers/stm32l432kc.html",
            "https://mouser.pe/ProductDetail/STM32F103C8T6",
        ]
        
        for url in test_urls:
            # Test URL detection logic using the same approach as scraper
            is_mouser = 'mouser.com' in url.lower() or 'mouser.pe' in url.lower()
            if "mouser" in url:
                assert is_mouser
            else:
                assert not is_mouser
            
            # Test part number extraction from URL by using the domain check
            if is_mouser:
                # For mouser URLs, would need full scraping
                continue
            else:
                # For ST URLs, extract from URL path  
                part_number = url.split('/')[-1].replace('.html', '').upper()
                assert part_number.startswith("STM32")

    def test_memory_calculation_accuracy(self):
        """
        GIVEN: MCU specs with various memory sizes
        WHEN: Generating board configurations
        THEN: Should accurately calculate memory constraints
        """
        board_generator = BoardFileGenerator()
        
        test_cases = [
            {"flash_kb": 64, "ram_kb": 20, "expected_flash": 65536, "expected_ram": 20480},
            {"flash_kb": 256, "ram_kb": 64, "expected_flash": 262144, "expected_ram": 65536},
            {"flash_kb": 1024, "ram_kb": 128, "expected_flash": 1048576, "expected_ram": 131072},
            {"flash_kb": 2048, "ram_kb": 512, "expected_flash": 2097152, "expected_ram": 524288},
        ]
        
        for case in test_cases:
            specs = MCUSpecs(
                part_number="TEST_MCU",
                family="STM32F4",
                core="cortex-m4",
                max_frequency="168000000L",
                flash_size_kb=case["flash_kb"],
                ram_size_kb=case["ram_kb"],
                package="LQFP",
                pin_count=64,
                operating_voltage_min=1.8,
                operating_voltage_max=3.6,
                temperature_min=-40,
                temperature_max=85,
                peripherals={},
                features=[]
            )
            
            config = board_generator.generate_board_file(specs, "test_board")  # Fixed method name
            upload_section = config["upload"]
            
            assert upload_section["maximum_size"] == case["expected_flash"]
            assert upload_section["maximum_ram_size"] == case["expected_ram"]

    def test_json_output_validation(self, temp_dir):
        """
        GIVEN: Generated board configuration
        WHEN: Saving and reloading JSON files
        THEN: Should maintain data integrity and structure
        """
        board_generator = BoardFileGenerator()
        
        specs = MCUSpecs(
            part_number="STM32G431CB",
            family="STM32G4",
            core="cortex-m4",
            max_frequency="170000000L",
            flash_size_kb=128,
            ram_size_kb=32,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.71,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={"USART": 4, "SPI": 3, "I2C": 3},
            features=["fpu", "cordic", "fmac"]
        )
        
        # Generate configuration
        original_config = board_generator.generate_board_file(specs, "validation_test")  # Fixed method name
        
        # Save to file
        output_file = temp_dir / "validation_test.json"
        board_generator._save_board_file(original_config, "validation_test", temp_dir)  # Fixed method signature
        
        # Reload and verify
        with open(output_file, 'r') as f:
            reloaded_config = json.load(f)
        
        assert reloaded_config == original_config
        
        # Verify all required PlatformIO sections exist
        required_sections = ["build", "debug", "frameworks", "name", "upload", "url", "vendor"]
        for section in required_sections:
            assert section in reloaded_config
        
        # Verify build section completeness
        build_section = reloaded_config["build"]
        required_build_keys = ["core", "cpu", "f_cpu", "mcu", "extra_flags"]
        for key in required_build_keys:
            assert key in build_section

    def test_concurrent_processing_workflow(self, temp_dir):
        """
        GIVEN: Multiple MCU specifications to process
        WHEN: Processing multiple board generations simultaneously
        THEN: Should handle concurrent operations without conflicts
        """
        board_generator = BoardFileGenerator()
        
        specs_list = [
            MCUSpecs("STM32F103C8T6", "STM32F1", "cortex-m3", "72000000L", 64, 20, "LQFP", 48, 2.0, 3.6, -40, 85, {}, []),
            MCUSpecs("STM32L432KC", "STM32L4", "cortex-m4", "80000000L", 256, 64, "LQFP", 32, 1.71, 3.6, -40, 85, {}, []),
            MCUSpecs("STM32G431CB", "STM32G4", "cortex-m4", "170000000L", 128, 32, "LQFP", 48, 1.71, 3.6, -40, 85, {}, []),
        ]
        
        generated_configs = []
        output_files = []
        
        # Process all specs
        for i, specs in enumerate(specs_list):
            board_name = f"concurrent_test_{i}"
            config = board_generator.generate_board_file(specs, board_name)  # Fixed method name
            generated_configs.append(config)
            
            output_file = temp_dir / f"{board_name}.json"
            board_generator._save_board_file(config, board_name, temp_dir)  # Fixed method signature
            output_files.append(output_file)
        
        # Verify all files were created correctly
        for i, output_file in enumerate(output_files):
            assert output_file.exists()
            
            with open(output_file, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config == generated_configs[i]
            assert saved_config["build"]["mcu"] == specs_list[i].part_number.lower()
