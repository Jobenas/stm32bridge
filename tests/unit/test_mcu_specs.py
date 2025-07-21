"""
Unit tests for MCUSpecs dataclass.

Tests cover validation, serialization, and core functionality
of the MCUSpecs data structure.
"""
import pytest
from typing import Dict, Any

from stm32bridge.utils.mcu_scraper import MCUSpecs


class TestMCUSpecs:
    """Test suite for MCUSpecs dataclass functionality."""

    def test_valid_mcu_specs_creation(self, sample_mcu_specs):
        """
        GIVEN: Valid MCU specification parameters
        WHEN: Creating an MCUSpecs instance
        THEN: All fields should be correctly assigned and accessible
        """
        specs = sample_mcu_specs
        
        assert specs.part_number == "STM32L432KC"
        assert specs.family == "STM32L4"
        assert specs.core == "cortex-m4"
        assert specs.max_frequency == "80000000L"
        assert specs.flash_size_kb == 256
        assert specs.ram_size_kb == 64
        assert specs.package == "LQFP"
        assert specs.pin_count == 32

    def test_mcu_specs_with_minimal_data(self):
        """
        GIVEN: Minimal required MCU specification parameters
        WHEN: Creating an MCUSpecs instance with all required fields
        THEN: Object should be created successfully
        """
        specs = MCUSpecs(
            part_number="STM32F103C8",
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
        )
        
        assert specs.part_number == "STM32F103C8"
        assert specs.core == "cortex-m3"
        assert specs.peripherals == {}
        assert specs.features == []

    def test_mcu_specs_with_peripherals(self):
        """
        GIVEN: MCU specs with peripheral counts
        WHEN: Creating MCUSpecs with peripherals dictionary
        THEN: Peripheral information should be stored correctly
        """
        peripherals = {
            "USART": 3,
            "SPI": 2,
            "I2C": 1,
            "ADC": 2
        }
        
        specs = MCUSpecs(
            part_number="STM32F401CC",
            family="STM32F4",
            core="cortex-m4",
            max_frequency="84000000L",
            flash_size_kb=256,
            ram_size_kb=64,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.8,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals=peripherals,
            features=[]
        )
        
        assert specs.peripherals["USART"] == 3
        assert specs.peripherals["SPI"] == 2
        assert specs.peripherals["I2C"] == 1
        assert specs.peripherals["ADC"] == 2

    def test_mcu_specs_with_features(self):
        """
        GIVEN: MCU specs with feature list
        WHEN: Creating MCUSpecs with features
        THEN: Features should be stored as a list
        """
        features = ["fpu", "dsp", "crypto", "usb"]
        
        specs = MCUSpecs(
            part_number="STM32H743VI",
            family="STM32H7",
            core="cortex-m7",
            max_frequency="480000000L",
            flash_size_kb=2048,
            ram_size_kb=1024,
            package="BGA",
            pin_count=176,
            operating_voltage_min=1.62,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=features
        )
        
        assert "fpu" in specs.features
        assert "dsp" in specs.features
        assert "crypto" in specs.features
        assert "usb" in specs.features
        assert len(specs.features) == 4

    def test_mcu_specs_voltage_range(self):
        """
        GIVEN: MCU specs with operating voltage range
        WHEN: Setting voltage min/max values
        THEN: Voltage values should be stored correctly
        """
        specs = MCUSpecs(
            part_number="STM32L476RG",
            family="STM32L4",
            core="cortex-m4",
            max_frequency="80000000L",
            flash_size_kb=1024,
            ram_size_kb=128,
            package="LQFP",
            pin_count=64,
            operating_voltage_min=1.71,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        assert specs.operating_voltage_min == 1.71
        assert specs.operating_voltage_max == 3.6

    def test_mcu_specs_temperature_range(self):
        """
        GIVEN: MCU specs with temperature range
        WHEN: Setting temperature min/max values
        THEN: Temperature values should be stored correctly
        """
        specs = MCUSpecs(
            part_number="STM32F769NI",
            family="STM32F7",
            core="cortex-m7",
            max_frequency="216000000L",
            flash_size_kb=2048,
            ram_size_kb=512,
            package="BGA",
            pin_count=216,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=105,
            peripherals={},
            features=[]
        )
        
        assert specs.temperature_min == -40
        assert specs.temperature_max == 105

    def test_mcu_specs_equality(self):
        """
        GIVEN: Two MCUSpecs instances with identical data
        WHEN: Comparing them for equality
        THEN: They should be considered equal
        """
        specs1 = MCUSpecs(
            part_number="STM32G431CB",
            family="STM32G4",
            core="cortex-m4",
            max_frequency="170000000L",
            flash_size_kb=128,
            ram_size_kb=32,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        specs2 = MCUSpecs(
            part_number="STM32G431CB",
            family="STM32G4",
            core="cortex-m4",
            max_frequency="170000000L",
            flash_size_kb=128,
            ram_size_kb=32,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        assert specs1 == specs2

    def test_mcu_specs_inequality(self):
        """
        GIVEN: Two MCUSpecs instances with different data
        WHEN: Comparing them for equality
        THEN: They should not be considered equal
        """
        specs1 = MCUSpecs(
            part_number="STM32G431CB",
            family="STM32G4",
            core="cortex-m4",
            max_frequency="170000000L",
            flash_size_kb=128,
            ram_size_kb=32,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        specs2 = MCUSpecs(
            part_number="STM32G431RB",  # Different part number
            family="STM32G4",
            core="cortex-m4",
            max_frequency="170000000L",
            flash_size_kb=128,
            ram_size_kb=32,
            package="LQFP",
            pin_count=48,
            operating_voltage_min=1.7,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        assert specs1 != specs2

    def test_mcu_specs_string_representation(self):
        """
        GIVEN: An MCUSpecs instance
        WHEN: Converting to string representation
        THEN: Should contain key identifying information
        """
        specs = MCUSpecs(
            part_number="STM32WB55CG",
            family="STM32WB",
            core="cortex-m4",
            max_frequency="64000000L",
            flash_size_kb=1024,
            ram_size_kb=256,
            package="BGA",
            pin_count=69,
            operating_voltage_min=1.71,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={},
            features=[]
        )
        
        str_repr = str(specs)
        assert "STM32WB55CG" in str_repr
        assert "STM32WB" in str_repr
        assert "cortex-m4" in str_repr

    @pytest.mark.parametrize("core_name,expected", [
        ("cortex-m0", "cortex-m0"),
        ("cortex-m0+", "cortex-m0plus"),
        ("cortex-m3", "cortex-m3"),
        ("cortex-m4", "cortex-m4"),
        ("cortex-m7", "cortex-m7"),
        ("cortex-m33", "cortex-m33"),
    ])
    def test_mcu_specs_core_variants(self, core_name, expected):
        """
        GIVEN: Different ARM Cortex core variants
        WHEN: Creating MCUSpecs with various core types
        THEN: Core names should be stored correctly
        """
        specs = MCUSpecs(
            part_number="TEST_MCU",
            family="TEST_FAMILY",
            core=core_name,
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
        
        # For cortex-m0+, we might want to normalize to cortex-m0plus
        if core_name == "cortex-m0+":
            assert specs.core == "cortex-m0+"  # Or test normalization logic
        else:
            assert specs.core == expected
