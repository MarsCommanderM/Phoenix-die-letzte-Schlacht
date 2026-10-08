cmake_minimum_required(VERSION 3.22)

# O3DE discovers this gem through project.json external_subdirectories and
# descends into Code/, where the build targets are declared.

add_subdirectory(Code)
