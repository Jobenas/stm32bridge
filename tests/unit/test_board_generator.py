"""
Unit tests for BoardFileGenerator class.

Tests cover board file generation, JSON formatting,
and configuration creation functionality.
"""
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from stm32bridge.utils.board_generator import BoardFileGenerator
from stm32bridge.utils.mcu_scraper import MCUSpecs


class TestBoardFileGenerator:
    """Test suite for BoardFileGenerator functionality."""

    def test_board_generator_initialization(self, board_generator):
        """
        GIVEN: A need to create board files
        WHEN: Initializing BoardFileGenerator
        THEN: Instance should be created successfully
        """
        assert isinstance(board_generator, BoardFileGenerator)

    def test_generate_board_file_basic(self, board_generator, sample_mcu_specs):
        """
        GIVEN: Valid MCU specifications
        WHEN: Generating board configuration
        THEN: Should return a complete board configuration dictionary
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        
        assert isinstance(config, dict)
        assert "build" in config
        assert "debug" in config
        assert "frameworks" in config
        assert "name" in config
        assert "upload" in config
        assert "url" in config
        assert "vendor" in config

    def test_generate_board_file_build_section(self, board_generator, sample_mcu_specs):
        """
        GIVEN: MCU specs with STM32L432KC details
        WHEN: Generating board configuration build section
        THEN: Build section should contain correct STM32L4 configuration
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        build_section = config["build"]
        
        assert build_section["core"] == "stm32"
        assert build_section["cpu"] == "cortex-m4"
        assert build_section["f_cpu"] == "80000000L"
        assert build_section["mcu"] == "stm32l432kc"
        assert "STM32L432KC" in build_section["extra_flags"]
        assert "STM32L4" in build_section["extra_flags"]

    def test_generate_board_file_debug_section(self, board_generator, sample_mcu_specs):
        """
        GIVEN: MCU specs for debugging configuration
        WHEN: Generating board configuration debug section
        THEN: Debug section should contain appropriate debug settings
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        debug_section = config["debug"]
        
        assert debug_section["jlink_device"] == "STM32L432KC"
        assert "stm32l4x" in debug_section["openocd_target"]
        assert debug_section["svd_path"] == "STM32L432KC.svd"

    def test_generate_board_file_upload_section(self, board_generator, sample_mcu_specs):
        """
        GIVEN: MCU specs with memory information
        WHEN: Generating board configuration upload section
        THEN: Upload section should reflect memory constraints
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        upload_section = config["upload"]
        
        # 256KB flash = 262144 bytes
        assert upload_section["maximum_size"] == 262144
        # 64KB RAM = 65536 bytes
        assert upload_section["maximum_ram_size"] == 65536
        assert upload_section["protocol"] == "stlink"
        assert "stlink" in upload_section["protocols"]
        assert "jlink" in upload_section["protocols"]

    def test_generate_board_file_frameworks(self, board_generator, sample_mcu_specs):
        """
        GIVEN: STM32 MCU specifications
        WHEN: Generating board configuration frameworks
        THEN: Should include appropriate STM32 frameworks
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        frameworks = config["frameworks"]
        
        assert "arduino" in frameworks
        assert "stm32cube" in frameworks

    def test_generate_board_file_name_generation(self, board_generator, sample_mcu_specs):
        """
        GIVEN: MCU specs with memory information
        WHEN: Generating board name
        THEN: Name should include part number and memory details
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        name = config["name"]
        
        assert "STM32L432KC" in name
        assert "256KB flash" in name
        assert "64KB RAM" in name

    def test_generate_board_file_different_mcu(self, board_generator, sample_stm32f103_specs):
        """
        GIVEN: Different MCU specifications (STM32F103)
        WHEN: Generating board configuration
        THEN: Should generate appropriate F1 series configuration
        """
        config = board_generator.generate_board_file(sample_stm32f103_specs, "test_board")
        build_section = config["build"]
        
        assert build_section["cpu"] == "cortex-m3"
        assert build_section["f_cpu"] == "72000000L"
        assert build_section["mcu"] == "stm32f103c8t6"
        assert "STM32F103C8T6" in build_section["extra_flags"]
        assert "STM32F1" in build_section["extra_flags"]

    def test_save_board_file(self, board_generator, sample_mcu_specs, temp_dir):
        """
        GIVEN: Generated board configuration and output directory
        WHEN: Saving board file to disk
        THEN: JSON file should be created with correct content
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        output_file = temp_dir / "test_board.json"
        
        board_generator._save_board_file(config, "test_board", temp_dir)
        
        assert output_file.exists()
        
        # Verify file content
        with open(output_file, 'r') as f:
            saved_config = json.load(f)
        
        assert saved_config == config
        assert saved_config["build"]["mcu"] == "stm32l432kc"

    def test_save_board_file_creates_directory(self, board_generator, sample_mcu_specs, temp_dir):
        """
        GIVEN: Output path with non-existent directory
        WHEN: Saving board file
        THEN: Directory should be created automatically
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        nested_dir = temp_dir / "boards" / "stm32"
        output_file = nested_dir / "test_board.json"
        
        board_generator._save_board_file(config, "test_board", nested_dir)
        
        assert output_file.exists()
        assert nested_dir.exists()

    def test_generate_extra_flags(self, board_generator):
        """
        GIVEN: MCU part number and family
        WHEN: Generating extra compiler flags
        THEN: Should include appropriate defines and HSE value
        """
        specs = MCUSpecs(
            part_number="STM32F407VG",
            family="STM32F4",
            core="cortex-m4",
            max_frequency="168000000L",
            flash_size_kb=1024,
            ram_size_kb=192,
            package="LQFP",
            pin_count=100,
            operating_voltage_min=1.8,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        config = board_generator.generate_board_file(specs, "test_board")
        extra_flags = config["build"]["extra_flags"]
        
        assert "-DSTM32F407VG" in extra_flags
        assert "-DSTM32F4" in extra_flags
        assert "-DHSE_VALUE=8000000" in extra_flags

    def test_board_config_json_serializable(self, board_generator, sample_mcu_specs):
        """
        GIVEN: Generated board configuration
        WHEN: Serializing to JSON
        THEN: Should serialize without errors and maintain structure
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        
        # Should not raise exception
        json_string = json.dumps(config, indent=2)
        
        # Should be able to deserialize back
        parsed_config = json.loads(json_string)
        assert parsed_config == config

    @pytest.mark.parametrize("family,expected_target", [
        ("STM32F1", "stm32f1x"),
        ("STM32F4", "stm32f4x"),
        ("STM32L4", "stm32l4x"),
        ("STM32H7", "stm32h7x"),
        ("STM32G4", "stm32g4x"),
    ])
    def test_openocd_target_mapping(self, board_generator, family, expected_target):
        """
        GIVEN: Different STM32 families
        WHEN: Generating debug configuration
        THEN: Should map to correct OpenOCD target
        """
        specs = MCUSpecs(
            part_number="TEST_MCU",
            family=family,
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
        
        config = board_generator.generate_board_file(specs, "test_board")
        openocd_target = config["debug"]["openocd_target"]
        
        assert expected_target in openocd_target

    def test_memory_size_calculations(self, board_generator):
        """
        GIVEN: MCU specs with different memory sizes
        WHEN: Generating upload configuration
        THEN: Should correctly calculate byte values from KB
        """
        specs = MCUSpecs(
            part_number="STM32F767ZI",
            family="STM32F7",
            core="cortex-m7",
            max_frequency="216000000L",
            flash_size_kb=2048,  # 2MB
            ram_size_kb=512,     # 512KB
            package="BGA",
            pin_count=144,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        config = board_generator.generate_board_file(specs, "test_board")
        upload_section = config["upload"]
        
        # 2048KB = 2,097,152 bytes
        assert upload_section["maximum_size"] == 2048 * 1024
        # 512KB = 524,288 bytes
        assert upload_section["maximum_ram_size"] == 512 * 1024

    def test_hwids_generation(self, board_generator, sample_mcu_specs):
        """
        GIVEN: STM32 MCU specifications
        WHEN: Generating hardware IDs
        THEN: Should include standard ST Microelectronics USB IDs
        """
        config = board_generator.generate_board_file(sample_mcu_specs, "test_board")
        hwids = config["build"]["hwids"]
        
        assert len(hwids) > 0
        # ST Microelectronics vendor ID
        assert any("0x0483" in hwid for hwid in hwids)
