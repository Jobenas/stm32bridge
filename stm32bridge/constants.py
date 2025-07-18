"""
Constants and configuration for STM32Bridge.
"""

# MCU family mappings
MCU_FAMILIES = {
    "STM32F0": {"hal_driver": "STM32F0xx_HAL_Driver", "cmsis": "STM32F0xx", "cortex": "cortex-m0"},
    "STM32F1": {"hal_driver": "STM32F1xx_HAL_Driver", "cmsis": "STM32F1xx", "cortex": "cortex-m3"},
    "STM32F2": {"hal_driver": "STM32F2xx_HAL_Driver", "cmsis": "STM32F2xx", "cortex": "cortex-m3"},
    "STM32F3": {"hal_driver": "STM32F3xx_HAL_Driver", "cmsis": "STM32F3xx", "cortex": "cortex-m4"},
    "STM32F4": {"hal_driver": "STM32F4xx_HAL_Driver", "cmsis": "STM32F4xx", "cortex": "cortex-m4"},
    "STM32F7": {"hal_driver": "STM32F7xx_HAL_Driver", "cmsis": "STM32F7xx", "cortex": "cortex-m7"},
    "STM32G0": {"hal_driver": "STM32G0xx_HAL_Driver", "cmsis": "STM32G0xx", "cortex": "cortex-m0plus"},
    "STM32G4": {"hal_driver": "STM32G4xx_HAL_Driver", "cmsis": "STM32G4xx", "cortex": "cortex-m4"},
    "STM32H7": {"hal_driver": "STM32H7xx_HAL_Driver", "cmsis": "STM32H7xx", "cortex": "cortex-m7"},
    "STM32L0": {"hal_driver": "STM32L0xx_HAL_Driver", "cmsis": "STM32L0xx", "cortex": "cortex-m0plus"},
    "STM32L1": {"hal_driver": "STM32L1xx_HAL_Driver", "cmsis": "STM32L1xx", "cortex": "cortex-m3"},
    "STM32L4": {"hal_driver": "STM32L4xx_HAL_Driver", "cmsis": "STM32L4xx", "cortex": "cortex-m4"},
    "STM32L5": {"hal_driver": "STM32L5xx_HAL_Driver", "cmsis": "STM32L5xx", "cortex": "cortex-m33"},
    "STM32U5": {"hal_driver": "STM32U5xx_HAL_Driver", "cmsis": "STM32U5xx", "cortex": "cortex-m33"},
    "STM32WB": {"hal_driver": "STM32WBxx_HAL_Driver", "cmsis": "STM32WBxx", "cortex": "cortex-m4"},
}

# Common PlatformIO board mappings
BOARD_MAPPINGS = {
    "STM32F401RE": "nucleo_f401re",
    "STM32F103C8": "bluepill_f103c8",
    "STM32F407VG": "disco_f407vg",
    "STM32F429ZI": "nucleo_f429zi",
    "STM32F746ZG": "nucleo_f746zg",
    "STM32L476RG": "nucleo_l476rg",
    "STM32G474RE": "nucleo_g474re",
    "STM32H743ZI": "nucleo_h743zi",
    "STM32L432K": "nucleo_l432kc",  # Added for our test case
}

# Board descriptions for the list command
BOARD_DESCRIPTIONS = {
    "nucleo_f401re": "STM32 Nucleo F401RE",
    "bluepill_f103c8": "STM32F103C8T6 Blue Pill",
    "disco_f407vg": "STM32F407VG Discovery",
    "nucleo_f429zi": "STM32 Nucleo F429ZI",
    "nucleo_f746zg": "STM32 Nucleo F746ZG",
    "nucleo_l476rg": "STM32 Nucleo L476RG",
    "nucleo_g474re": "STM32 Nucleo G474RE",
    "nucleo_h743zi": "STM32 Nucleo H743ZI",
    "nucleo_l432kc": "STM32 Nucleo L432KC",
}
