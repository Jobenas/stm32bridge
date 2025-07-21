"""
Test fixtures for complex testing scenarios.

Provides realistic test data, mock responses, and
factory functions for comprehensive testing.
"""
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

import pytest
from factory.base import Factory
from factory.faker import Faker
from factory.declarations import SubFactory, LazyAttribute
from unittest.mock import Mock

from stm32bridge.utils.mcu_scraper import MCUSpecs


class MCUSpecsFactory(Factory):
    """
    Factory for generating MCUSpecs test instances.
    
    GIVEN: Need for realistic MCU specification data
    WHEN: Creating test scenarios with varied MCU specs
    THEN: Provides factory-generated MCU specifications
    """
    class Meta:
        model = MCUSpecs
    
    part_number = Faker('random_element', elements=[
        'STM32L432KC', 'STM32F103C8T6', 'STM32H743VI',
        'STM32G431CB', 'STM32WB55CG', 'STM32F407VG'
    ])
    
    family = LazyAttribute(lambda obj: f"STM32{obj.part_number[5:7]}")
    
    core = Faker('random_element', elements=[
        'cortex-m0', 'cortex-m0+', 'cortex-m3', 
        'cortex-m4', 'cortex-m7', 'cortex-m33'
    ])
    
    max_frequency = Faker('random_element', elements=[
        '48000000L', '72000000L', '80000000L', 
        '168000000L', '216000000L', '480000000L'
    ])
    
    flash_size_kb = Faker('random_element', elements=[
        32, 64, 128, 256, 512, 1024, 2048
    ])
    
    ram_size_kb = Faker('random_element', elements=[
        8, 16, 20, 32, 64, 96, 128, 256, 512, 1024
    ])
    
    package = Faker('random_element', elements=[
        'LQFP', 'UFQFPN', 'TSSOP', 'WLCSP', 'BGA'
    ])
    
    pin_count = Faker('random_element', elements=[
        28, 32, 48, 64, 100, 144, 176, 208
    ])
    
    operating_voltage_min = Faker('random_element', elements=[
        1.7, 1.71, 1.8, 2.0, 2.4
    ])
    
    operating_voltage_max = Faker('random_element', elements=[
        3.3, 3.6, 5.0, 5.5
    ])
    
    temperature_min = Faker('random_element', elements=[
        -40, -25, 0
    ])
    
    temperature_max = Faker('random_element', elements=[
        70, 85, 105, 125
    ])
    
    peripherals = Faker('pydict', nb_elements=5, value_types=[int])
    features = Faker('pylist', nb_elements=3, variable_nb_elements=True)


@pytest.fixture
def stm32l4_family_specs():
    """
    GIVEN: Need for STM32L4 family specifications
    WHEN: Testing L4-specific functionality
    THEN: Returns comprehensive L4 series MCU specs
    """
    return [
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
            peripherals={"USART": 3, "SPI": 3, "I2C": 2, "ADC": 1},
            features=["fpu", "usb", "crypto"]
        ),
        MCUSpecs(
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
            peripherals={"USART": 5, "SPI": 3, "I2C": 3, "ADC": 3},
            features=["fpu", "usb", "lcd", "crypto"]
        )
    ]


@pytest.fixture
def stm32f1_family_specs():
    """
    GIVEN: Need for STM32F1 family specifications
    WHEN: Testing F1-specific functionality
    THEN: Returns comprehensive F1 series MCU specs
    """
    return [
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
            peripherals={"USART": 3, "SPI": 2, "I2C": 2, "ADC": 2},
            features=[]
        ),
        MCUSpecs(
            part_number="STM32F103RBT6",
            family="STM32F1",
            core="cortex-m3",
            max_frequency="72000000L",
            flash_size_kb=128,
            ram_size_kb=20,
            package="LQFP",
            pin_count=64,
            operating_voltage_min=2.0,
            operating_voltage_max=3.6,
            temperature_min=-40,
            temperature_max=85,
            peripherals={"USART": 3, "SPI": 2, "I2C": 2, "ADC": 2},
            features=[]
        )
    ]


@pytest.fixture
def sample_html_responses():
    """
    GIVEN: Need for realistic HTML response data
    WHEN: Testing HTML parsing functionality
    THEN: Returns dictionary of sample HTML responses
    """
    return {
        "mouser_stm32l432": """
        <html>
            <head><title>STM32L432KCU6 - Ultra-low-power microcontroller</title></head>
            <body>
                <div class="product-header">
                    <h1>STM32L432KCU6</h1>
                    <span class="manufacturer">STMicroelectronics</span>
                </div>
                <div class="product-details">
                    <div class="specification">
                        <label>Core:</label>
                        <span>ARM Cortex-M4 with FPU</span>
                    </div>
                    <div class="specification">
                        <label>Max Frequency:</label>
                        <span>80 MHz</span>
                    </div>
                    <div class="specification">
                        <label>Flash Memory:</label>
                        <span>256 KB</span>
                    </div>
                    <div class="specification">
                        <label>SRAM:</label>
                        <span>64 KB</span>
                    </div>
                    <div class="specification">
                        <label>Package:</label>
                        <span>UFQFPN-28</span>
                    </div>
                </div>
            </body>
        </html>
        """,
        
        "st_stm32f103": """
        <html>
            <head><title>STM32F103C8T6 - Mainstream performance line</title></head>
            <body>
                <div class="product-overview">
                    <h1>STM32F103C8T6</h1>
                    <p class="product-line">Mainstream performance line, ARM Cortex-M3 MCU</p>
                </div>
                <section class="key-features">
                    <h2>Key Features</h2>
                    <ul>
                        <li>Core: ARM Cortex-M3</li>
                        <li>Operating frequency: Up to 72 MHz</li>
                        <li>Flash memory: 64 Kbytes</li>
                        <li>SRAM: 20 Kbytes</li>
                        <li>Package: LQFP48</li>
                        <li>Operating voltage: 2.0 to 3.6 V</li>
                        <li>Temperature range: -40°C to +85°C</li>
                    </ul>
                </section>
            </body>
        </html>
        """,
        
        "minimal_product_page": """
        <html>
            <head><title>STM32G431CB Product Page</title></head>
            <body>
                <h1>STM32G431CB</h1>
                <p>Cortex-M4 170MHz 128KB Flash 32KB RAM</p>
            </body>
        </html>
        """,
        
        "malformed_html": """
        <html>
            <head><title>STM32H743VI</title>
            <body>
                <h1>STM32H743VI</h1>
                <div>ARM Cortex-M7 core
                <p>480 MHz frequency
                <span>2 MB Flash
                <!-- Missing closing tags -->
        """,
        
        "no_stm32_content": """
        <html>
            <head><title>Generic Electronics Page</title></head>
            <body>
                <h1>Electronic Components</h1>
                <p>We sell various electronic components and modules.</p>
                <div>No specific STM32 information here.</div>
            </body>
        </html>
        """
    }


@pytest.fixture
def sample_board_configurations():
    """
    GIVEN: Need for sample PlatformIO board configurations
    WHEN: Testing board generation with varied inputs
    THEN: Returns collection of realistic board configurations
    """
    return {
        "stm32l432kc": {
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
        },
        
        "stm32f103c8t6": {
            "build": {
                "core": "stm32",
                "cpu": "cortex-m3",
                "extra_flags": "-DSTM32F103C8T6 -DSTM32F1 -DHSE_VALUE=8000000",
                "f_cpu": "72000000L",
                "hwids": [["0x0483", "0x3748"]],
                "mcu": "stm32f103c8t6",
                "product_line": "STM32F103xx",
                "variant": "STM32F103C8T6"
            },
            "debug": {
                "jlink_device": "STM32F103C8",
                "openocd_target": "stm32f1x",
                "svd_path": "STM32F103C8T6.svd"
            },
            "frameworks": ["arduino", "stm32cube"],
            "name": "STM32F103C8T6 (64KB flash, 20KB RAM)",
            "upload": {
                "maximum_ram_size": 20480,
                "maximum_size": 65536,
                "protocol": "stlink",
                "protocols": ["jlink", "stlink", "blackmagic", "serial"]
            },
            "url": "https://www.st.com/en/microcontrollers-microprocessors.html",
            "vendor": "ST"
        }
    }


@pytest.fixture
def mock_http_responses():
    """
    GIVEN: Need for mocked HTTP response objects
    WHEN: Testing HTTP request handling
    THEN: Returns configured mock response objects
    """
    def create_mock_response(status_code: int, content: str, headers: Optional[Dict[str, str]] = None) -> Mock:
        """Create a mock HTTP response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.content = content.encode('utf-8')
        mock_response.text = content
        mock_response.headers = headers or {}
        
        if status_code == 200:
            mock_response.raise_for_status.return_value = None
        else:
            mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        
        return mock_response
    
    return {
        "success": create_mock_response(200, "<html><body>Success</body></html>"),
        "not_found": create_mock_response(404, "<html><body>Not Found</body></html>"),
        "rate_limited": create_mock_response(429, "Rate Limited", {"Retry-After": "60"}),
        "server_error": create_mock_response(500, "Internal Server Error"),
        "timeout": create_mock_response(408, "Request Timeout")
    }


@pytest.fixture
def test_urls():
    """
    GIVEN: Need for realistic test URLs
    WHEN: Testing URL handling and validation
    THEN: Returns collection of test URLs for different scenarios
    """
    return {
        "mouser_urls": [
            "https://www.mouser.com/ProductDetail/STMicroelectronics/STM32L432KCU6",
            "https://mouser.pe/ProductDetail/STMicroelectronics/STM32F103C8T6",
            "http://www.mouser.dk/ProductDetail/STM32G431CBU6"
        ],
        "st_urls": [
            "https://www.st.com/en/microcontrollers-microprocessors/stm32l432kc.html",
            "https://www.st.com/en/microcontrollers/stm32f103c8t6.html",
            "https://www.st.com/content/st_com/en/products/microcontrollers/stm32g431cb.html"
        ],
        "invalid_urls": [
            "not-a-url",
            "ftp://wrong-protocol.com/file",
            "https://invalid-domain.xyz/product",
            "",
            "javascript:alert('xss')"
        ],
        "non_stm32_urls": [
            "https://www.digikey.com/product/arduino-uno",
            "https://www.example.com/random-page",
            "https://www.github.com/user/repo"
        ]
    }


@pytest.fixture
def complex_test_scenarios():
    """
    GIVEN: Need for complex multi-step test scenarios
    WHEN: Testing complete workflows and edge cases
    THEN: Returns structured test scenario data
    """
    return {
        "fallback_scenario": {
            "primary_url": "https://www.st.com/en/microcontrollers/stm32l476rg.html",
            "fallback_url": "https://www.mouser.com/ProductDetail/STM32L476RGT6",
            "expected_specs": {
                "part_number": "STM32L476RG",
                "family": "STM32L4",
                "core": "cortex-m4"
            }
        },
        "network_issues": {
            "urls": [
                "https://slow-server.com/timeout-url",
                "https://rate-limited.com/api/product",
                "https://unreachable.domain/product"
            ],
            "expected_behavior": "graceful_failure"
        },
        "data_validation": {
            "valid_inputs": ["STM32L432KC", "STM32F103C8T6", "STM32H743VI"],
            "invalid_inputs": ["INVALID123", "", None, "ATMEGA328P"],
            "edge_cases": ["stm32l432kc", "STM32l432KC", "STM32L432KC-extra"]
        }
    }
