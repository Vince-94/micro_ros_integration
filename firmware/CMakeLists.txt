# firmware/common/CMakeLists.txt
# Defines the firmware_common library with shared sources and headers


cmake_minimum_required(VERSION 3.20)
project(firmware_common LANGUAGES C CXX ASM)

# Collect all common firmware sources (C and C++)
file(GLOB FW_COMMON_SRC CONFIGURE_DEPENDS
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
)

# Create the firmware_common static library
add_library(firmware_common STATIC ${FW_COMMON_SRC})

# Public include directory for shared headers
# Root include is already added at the top-level, but we make sure it's exported
# so dependents of firmware_common can include them without extra setup.
target_include_directories(firmware_common PUBLIC
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Link against additional libraries if needed (e.g., common utilities)
# target_link_libraries(firmware_common PUBLIC some_lib)

# Optionally define an alias target for convenience
add_library(firmware::common ALIAS firmware_common)

message(STATUS "firmware_common library defined with sources: ${FW_COMMON_SRC}")