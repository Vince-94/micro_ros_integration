# platforms/rp2040/CMakeLists.txt
# Minimal platform file for RP2040 (Raspberry Pi Pico) that:
# - attempts to locate pico-sdk (third_party/pico-sdk or ENV PICO_SDK_PATH)
# - creates a platform_adapter static library
# - builds a firmware executable that links firmware_common and the adapter


cmake_minimum_required(VERSION 3.20)
project(rp2040_platform LANGUAGES C CXX ASM)


# Option to allow fetching pico-sdk if not found
option(ENABLE_PICO_SDK_FETCH "Allow fetching pico-sdk if not found" ON)

# Locate Pico SDK: prefer environment, then third_party/pico-sdk. If not found and
# ENABLE_PICO_SDK_FETCH is ON, try to fetch it via FetchContent.
if(DEFINED ENV{PICO_SDK_PATH})
  set(PICO_SDK_PATH $ENV{PICO_SDK_PATH})
  elseif(EXISTS "${CMAKE_SOURCE_DIR}/third_party/pico-sdk")
  set(PICO_SDK_PATH "${CMAKE_SOURCE_DIR}/third_party/pico-sdk")
endif()


if(NOT PICO_SDK_PATH AND ENABLE_PICO_SDK_FETCH)
  message(STATUS "Pico SDK not found locally; FetchContent will attempt to download it. This requires internet access at configure time.")
  include(FetchContent)
  FetchContent_Declare(pico_sdk
  GIT_REPOSITORY https://github.com/raspberrypi/pico-sdk.git
  GIT_TAG master
)
FetchContent_MakeAvailable(pico_sdk)
set(PICO_SDK_PATH ${pico_sdk_SOURCE_DIR})
endif()


if(NOT PICO_SDK_PATH)
  message(FATAL_ERROR "Pico SDK not found. Set PICO_SDK_PATH environment variable or add third_party/pico-sdk.\nSee https://github.com/raspberrypi/pico-sdk for instructions.")
endif()


# Import pico sdk and initialize
set(PICO_EXCLUDE_PICOTOOL ON CACHE BOOL "Skip building picotool")
if(NOT EXISTS ${PICO_SDK_PATH}/pico_sdk_init.cmake)
  message(FATAL_ERROR "pico_sdk_init.cmake not found in ${PICO_SDK_PATH}")
endif()

include(${PICO_SDK_PATH}/pico_sdk_init.cmake)
pico_sdk_init()


# Platform adapter: keep source inside platforms/rp2040/adapter.c
add_library(platform_adapter_rp2040 STATIC ${CMAKE_SOURCE_DIR}/platforms/rp2040/adapter.c)
target_include_directories(platform_adapter_rp2040 PUBLIC ${CMAKE_SOURCE_DIR}/include ${CMAKE_SOURCE_DIR}/platforms/rp2040)
target_link_libraries(platform_adapter_rp2040 PUBLIC pico_stdlib hardware_gpio hardware_timer)


# Ensure firmware_common target exists (added by firmware/CMakeLists.txt)
if(NOT TARGET firmware_common)
  message(WARNING "Target 'firmware_common' not found. Ensure firmware/CMakeLists.txt defines it.")
endif()


# Decide firmware entrypoint: prefer firmware/platforms/rp2040/main.c then firmware/main.c
if(EXISTS "${CMAKE_SOURCE_DIR}/firmware/platforms/rp2040/main.c")
  set(FW_ENTRY "${CMAKE_SOURCE_DIR}/firmware/platforms/rp2040/main.c")
elseif(EXISTS "${CMAKE_SOURCE_DIR}/firmware/src/main.c")
  set(FW_ENTRY "${CMAKE_SOURCE_DIR}/firmware/src/main.c")
else()
  message(FATAL_ERROR "No firmware entrypoint found for rp2040. Add firmware/platforms/rp2040/main.c or firmware/src/main.c")
endif()


# add_executable(firmware_rp2040 ...)
add_executable(firmware_rp2040
  ${CMAKE_SOURCE_DIR}/firmware/src/main.c
  # add other firmware-specific sources here if needed
)
target_include_directories(firmware_rp2040 PUBLIC
  ${CMAKE_SOURCE_DIR}/include
  ${CMAKE_SOURCE_DIR}/firmware/src
)


target_link_libraries(firmware_rp2040 PRIVATE
  firmware_common
  platform_adapter_rp2040
  pico_stdlib
)

# Make the produced binary have a .elf extension and a friendly output name.
# pico_add_extra_outputs expects an ELF file as input so it can create UF2/etc.
set_target_properties(firmware_rp2040 PROPERTIES
  OUTPUT_NAME "firmware"   # resulting file: firmware.elf
  SUFFIX ".elf"
)


pico_add_extra_outputs(firmware_rp2040)


# Optional: set the board if you use pico_board support
# pico_set_board(firmware_rp2040 pico)


message(STATUS "RP2040 platform configured. Built targets: platform_adapter_rp2040, firmware_rp2040")