cmake_minimum_required(VERSION 3.20)
project(micro_ros_integration LANGUAGES C CXX ASM)


# Select target platform. Use -DPLATFORM=<rp2040|nucleo_f401re|esp32|host>
if(NOT DEFINED PLATFORM)
  message(FATAL_ERROR "Specify PLATFORM (e.g. -DPLATFORM=rp2040)")
endif()
message(STATUS "Building for PLATFORM='${PLATFORM}'")


# Helpful options
option(BUILD_EXAMPLES "Build example programs" ON)


# Add global include directory for public headers
if(EXISTS "${CMAKE_SOURCE_DIR}/include")
  include_directories(${CMAKE_SOURCE_DIR}/include)
endif()


# Add firmware common (if present)
if(EXISTS "${CMAKE_SOURCE_DIR}/firmware/CMakeLists.txt")
  add_subdirectory(firmware)
else()
  message(STATUS "No firmware/CMakeLists.txt found — ensure a firmware_common target exists or add firmware/CMakeLists.txt")
endif()


# Validate and include platform directory (skip for host)
if(NOT PLATFORM STREQUAL "host")
  set(PLATFORM_DIR "${CMAKE_SOURCE_DIR}/platforms/${PLATFORM}")
  if(NOT EXISTS "${PLATFORM_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "Unknown or missing platform: ${PLATFORM}\nExpected: ${PLATFORM_DIR}/CMakeLists.txt")
  endif()
  add_subdirectory(${PLATFORM_DIR})
endif()


# Examples: iterate subdirs and add them if they provide a CMakeLists.txt
if(BUILD_EXAMPLES AND EXISTS "${CMAKE_SOURCE_DIR}/examples")
  file(GLOB CHILDREN RELATIVE ${CMAKE_SOURCE_DIR}/examples ${CMAKE_SOURCE_DIR}/examples/*)
  foreach(child ${CHILDREN})
    if(EXISTS "${CMAKE_SOURCE_DIR}/examples/${child}/CMakeLists.txt")
      add_subdirectory(${CMAKE_SOURCE_DIR}/examples/${child})
    endif()
  endforeach()
endif()


# Install targets and packaging helpers can be added here
message(STATUS "Configuration complete. Use -DPLATFORM=<your_target> and optionally -DCMAKE_TOOLCHAIN_FILE=<path> to cross-compile.")