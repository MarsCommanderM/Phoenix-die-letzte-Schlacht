cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixWorld)

set(FILES
    Code/Source/PhoenixWorldModule.cpp
    Code/Source/PhoenixWorldSystemComponent.cpp
    Code/Include/Phoenix/PhoenixWorld/PhoenixWorld.h
    Code/Include/Phoenix/World/PhoenixWorldCell.h
    Code/Include/Phoenix/World/PhoenixWorldSystemComponent.h
)
