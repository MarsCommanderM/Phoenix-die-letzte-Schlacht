cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixTools)

set(FILES
    Code/Source/PhoenixToolsModule.cpp
    Code/Source/PhoenixToolsSystemComponent.cpp
    Code/Include/Phoenix/PhoenixTools/PhoenixTools.h
    Code/Include/Phoenix/Tools/PhoenixToolsSystemComponent.h
    Code/Include/Phoenix/Tools/PhoenixValidationResult.h
)
