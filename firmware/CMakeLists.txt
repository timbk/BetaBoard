cmake_minimum_required(VERSION 3.13)

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)
# include(pico_extras_import.cmake)
 
set(PICO_CXX_ENABLE_EXCEPTIONS 1)
project(betaBoard)
pico_sdk_init()

add_executable(betaBoard
    src/main.cpp
    src/version.c
)

target_compile_options(betaBoard PRIVATE -Wall ) # These all throw too many warning from SDK: -Wpedantic -Werror -Wextra

set_property(TARGET betaBoard PROPERTY CXX_STANDARD 20)

target_link_libraries(betaBoard PRIVATE
    pico_stdlib
    # hardware_pio # for i2s
    hardware_dma # for ADC
    hardware_irq # ADC data ready gpio interrupt
    # hardware_spi # for ADC interface
    # hardware_i2c # for configuring the DAC
    # hardware_pwm # for clocking the ADC
    hardware_adc # For RP2040 internal temperature sensor
)
pico_add_extra_outputs(betaBoard)

# add url via pico_set_program_url
# example_auto_set_url(betaBoard)

pico_enable_stdio_usb(betaBoard 1)
pico_enable_stdio_uart(betaBoard 0)
