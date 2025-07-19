"""
Demo script to show the board generation functionality working
"""
from stm32bridge.utils.mcu_scraper import MCUSpecs
from stm32bridge.utils.board_generator import BoardFileGenerator
import json

# Create a mock MCUSpecs for demonstration
demo_specs = MCUSpecs(
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

# Generate board file
generator = BoardFileGenerator()
board_config = generator.generate_board_file(demo_specs, "demo_l432kc", None)

# Save the demo board file
import os
os.makedirs("test_output/boards", exist_ok=True)
with open("test_output/boards/demo_l432kc.json", "w") as f:
    json.dump(board_config, f, indent=2)

print("✅ Demo board file generated successfully!")
print("📍 Location: test_output/boards/demo_l432kc.json")
print("\n📋 Generated Board Configuration:")
print(json.dumps(board_config, indent=2))
