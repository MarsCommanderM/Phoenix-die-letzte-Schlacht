cmake_minimum_required(VERSION 3.22)

# Phoenix O3DE project entry point.
#
# EngineFinder.cmake is written by the engine when the project is registered
# (`o3de register --project-path .`), so it is included OPTIONAL and is not
# committed: it records a machine-local engine path.
include(${CMAKE_CURRENT_LIST_DIR}/cmake/EngineFinder.cmake OPTIONAL)

find_package(o3de REQUIRED)

project(Phoenix
    LANGUAGES C CXX
    VERSION 0.1.0
)

o3de_initialize()
