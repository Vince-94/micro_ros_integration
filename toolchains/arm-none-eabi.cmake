# toolchains/arm-none-eabi.cmake
# Cross-compilation toolchain for RP2040 (Cortex-M0+)

# Make try_compile create static libs (avoid linking small executables that need newlib syscalls)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)

# Cross compiler executables (must be in PATH)
set(CMAKE_C_COMPILER   arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)

# CPU flags for RP2040 (Cortex-M0+ Thumb)
set(RP2040_CPU_FLAGS "-mcpu=cortex-m0plus -mthumb")

# Default flags (allow CMake to append/override per-config)
set(CMAKE_C_FLAGS_INIT    "${RP2040_CPU_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_INIT  "${RP2040_CPU_FLAGS} -Wall -Wextra -fno-exceptions -fno-rtti")
set(CMAKE_ASM_FLAGS_INIT  "${RP2040_CPU_FLAGS}")

# Ensure assembler sees the flags (important for crt/asm)
set(CMAKE_ASM_FLAGS "${CMAKE_ASM_FLAGS_INIT}" CACHE STRING "ASM flags" FORCE)

# Do NOT include -specs=nosys.specs here; pico-sdk will add it where appropriate.
set(CMAKE_EXE_LINKER_FLAGS_INIT "${RP2040_CPU_FLAGS}")
set(CMAKE_MODULE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS_INIT}")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS_INIT}")

# Ensure host programs (picotool etc.) are found and built with host compiler
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
