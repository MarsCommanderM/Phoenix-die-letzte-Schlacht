cmake_minimum_required(VERSION 3.22)

# O3DE project CMake integration.
# The O3DE project template supplies the engine-level functions/macros.
# Keep project-specific source declarations in Phoenix_files.cmake.

set(PHOENIX_PROJECT_NAME Phoenix)

include(${CMAKE_CURRENT_LIST_DIR}/Phoenix_files.cmake)

if(EXISTS ${CMAKE_CURRENT_LIST_DIR}/Phoenix_autogen_files.cmake)
    include(${CMAKE_CURRENT_LIST_DIR}/Phoenix_autogen_files.cmake)
endif()
