cmake_minimum_required(VERSION 3.16)

project(CheckForge VERSION 0.1.0 LANGUAGES CXX)

# Default to an optimized build. Without this CMAKE_BUILD_TYPE is empty and g++ runs
# with NO optimization (-O0), which throttles nodes/sec and therefore search depth.
# Release (-O3 -DNDEBUG) is the cheapest, zero-risk strength lever (exp016).
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

enable_testing()

add_subdirectory(engine)
