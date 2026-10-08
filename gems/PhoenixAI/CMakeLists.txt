cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixAI)

set(FILES
    Code/Source/PhoenixAIModule.cpp
    Code/Source/PhoenixAISystemComponent.cpp
    Code/Include/Phoenix/AI/PhoenixAIContext.h
    Code/Include/Phoenix/AI/PhoenixAIState.h
    Code/Include/Phoenix/AI/PhoenixAISystemComponent.h
    Code/Include/Phoenix/PhoenixAI/PhoenixAI.h
)
