"""
Working unit tests for STM32Bridge - Basic MCU Specs functionality.

These tests are designed to actually work with the existing codebase.
"""
import pytest
from stm32bridge.utils.mcu_scraper import MCUSpecs


class TestMCUSpecsWorking:
    """Working tests for MCUSpecs dataclass."""

    def test_mcu_specs_creation_with_all_fields(self):
        """
        GIVEN: Complete MCU specification parameters
        WHEN: Creating an MCUSpecs instance
        THEN: All fields should be correctly assigned
        """
        specs = MCUSpecs(
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
            peripherals={"USART": 3, "SPI": 3, "I2C": 2},
            features=["fpu", "usb", "crypto"]
        )
        
        assert specs.part_number == "STM32L432KC"
        assert specs.family == "STM32L4" 
        assert specs.core == "cortex-m4"
        assert specs.flash_size_kb == 256
        assert specs.ram_size_kb == 64
        assert specs.peripherals["USART"] == 3
        assert "fpu" in specs.features

    def test_mcu_specs_minimal_required_fields(self):
        """
        GIVEN: MCU specs with minimal required data
        WHEN: Creating MCUSpecs with empty collections
        THEN: Should create successfully with empty peripherals and features
        """
        specs = MCUSpecs(
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
        )
        
        assert specs.part_number == "STM32F103C8T6"
        assert specs.peripherals == {}
        assert specs.features == []

    def test_mcu_specs_equality(self):
        """
        GIVEN: Two identical MCUSpecs instances
        WHEN: Comparing them for equality
        THEN: Should be equal
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
