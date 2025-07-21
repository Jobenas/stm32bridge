"""
Pytest configuration and shared fixtures for STM32Bridge tests.

This module provides common test fixtures and configuration
for both unit and integration tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, MagicMock

from stm32bridge.utils.mcu_scraper import MCUSpecs
from stm32bridge.utils.board_generator import BoardFileGenerator


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    GIVEN: A need for temporary directory operations
    WHEN: Tests require file system operations
    THEN: Provides a clean temporary directory that's automatically cleaned up
    """
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_mcu_specs() -> MCUSpecs:
    """
    GIVEN: Tests need valid MCU specifications
    WHEN: Creating test scenarios for board generation
    THEN: Returns a well-formed MCUSpecs object with realistic STM32L432KC data
    """
    return MCUSpecs(
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
        peripherals={
            "USART": 3,
            "SPI": 3,
            "I2C": 2,
            "ADC": 1,
            "TIMER": 7,
            "USB": 1
        },
        features=["fpu", "usb", "crypto"]
    )


@pytest.fixture
def sample_stm32f103_specs() -> MCUSpecs:
    """
    GIVEN: Tests need STM32F1 series specifications
    WHEN: Testing core detection and board generation for F1 series
    THEN: Returns MCUSpecs for STM32F103C8T6 with correct Cortex-M3 core
    """
    return MCUSpecs(
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
        peripherals={
            "USART": 3,
            "SPI": 2,
            "I2C": 2,
            "ADC": 2,
            "TIMER": 4
        },
        features=[]
    )


@pytest.fixture
def sample_board_config() -> Dict[str, Any]:
    """
    GIVEN: Tests need valid PlatformIO board configuration
    WHEN: Verifying board file generation output
    THEN: Returns a complete board configuration dictionary
    """
    return {
        "build": {
            "core": "stm32",
            "cpu": "cortex-m4",
            "extra_flags": "-DSTM32L432KC -DSTM32L4 -DHSE_VALUE=8000000",
            "f_cpu": "80000000L",
            "hwids": [["0x0483", "0x374B"]],
            "mcu": "stm32l432kc",
            "product_line": "STM32L432xx",
            "variant": "STM32L432KC"
        },
        "debug": {
            "jlink_device": "STM32L432KC",
            "openocd_target": "stm32l4x",
            "svd_path": "STM32L432KC.svd"
        },
        "frameworks": ["arduino", "stm32cube"],
        "name": "STM32L432KC (256KB flash, 64KB RAM)",
        "upload": {
            "maximum_ram_size": 65536,
            "maximum_size": 262144,
            "protocol": "stlink",
            "protocols": ["jlink", "stlink", "blackmagic", "mbed"]
        },
        "url": "https://www.st.com/en/microcontrollers-microprocessors.html",
        "vendor": "ST"
    }


@pytest.fixture
def mock_requests_response():
    """
    GIVEN: Tests need to mock HTTP responses
    WHEN: Testing URL scraping functionality
    THEN: Returns a mock response object with common methods
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.content = b"<html><body>Mock HTML content</body></html>"
    mock_response.text = "Mock HTML content"
    return mock_response


@pytest.fixture
def mock_beautiful_soup():
    """
    GIVEN: Tests need to mock BeautifulSoup parsing
    WHEN: Testing HTML parsing without actual HTTP requests
    THEN: Returns a mock BeautifulSoup object with common methods
    """
    mock_soup = Mock()
    mock_soup.get_text.return_value = "mock page text content"
    mock_soup.find.return_value = None
    mock_soup.find_all.return_value = []
    return mock_soup


@pytest.fixture
def board_generator() -> BoardFileGenerator:
    """
    GIVEN: Tests need a board file generator instance
    WHEN: Testing board file generation functionality
    THEN: Returns a fresh BoardFileGenerator instance
    """
    return BoardFileGenerator()


@pytest.fixture
def mouser_html_content() -> str:
    """
    GIVEN: Tests need realistic Mouser page content
    WHEN: Testing Mouser URL parsing
    THEN: Returns mock HTML with STM32 product information
    """
    return """
    <html>
        <head><title>STM32L432KCU6 - STMicroelectronics</title></head>
        <body>
            <h1>STM32L432KCU6</h1>
            <div class="product-details">
                <span>ARM Cortex-M4</span>
                <span>80 MHz</span>
                <span>256 KB Flash</span>
                <span>64 KB RAM</span>
                <span>UFQFPN-28</span>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def st_html_content() -> str:
    """
    GIVEN: Tests need realistic ST website content
    WHEN: Testing ST URL parsing
    THEN: Returns mock HTML with STM32 product information
    """
    return """
    <html>
        <head><title>STM32L432KC - Ultra-low-power microcontroller</title></head>
        <body>
            <h1>STM32L432KC</h1>
            <div class="specifications">
                <span>Core: ARM Cortex-M4</span>
                <span>Frequency: 80 MHz</span>
                <span>Flash: 256 Kbytes</span>
                <span>SRAM: 64 Kbytes</span>
            </div>
        </body>
    </html>
    """


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    GIVEN: Tests may create singleton instances
    WHEN: Running multiple tests that might affect global state
    THEN: Ensures clean state between tests
    """
    # Reset any module-level caches or singletons here if needed
    yield
    # Cleanup after test
