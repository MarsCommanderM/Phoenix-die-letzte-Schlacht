cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixCore)

set(FILES
    Code/Source/PhoenixCoreModule.cpp
    Code/Source/PhoenixCoreSystemComponent.cpp
    Code/Source/PhoenixDiagnostics.cpp
    Code/Source/PhoenixRuntimeService.cpp
    Code/Include/Phoenix/Core/PhoenixBuildInfo.h
    Code/Include/Phoenix/Core/PhoenixCoreSystemComponent.h
    Code/Include/Phoenix/Core/PhoenixDiagnostics.h
    Code/Include/Phoenix/Core/PhoenixIds.h
    Code/Include/Phoenix/Core/PhoenixResult.h
    Code/Include/Phoenix/Core/PhoenixRuntimeService.h
    Code/Include/Phoenix/Core/PhoenixTags.h
    Code/Include/Phoenix/Core/PhoenixTime.h
    Code/Include/Phoenix/Core/PhoenixTypes.h
    Code/Include/Phoenix/Core/PhoenixVersion.h
    Code/Include/Phoenix/PhoenixCore/PhoenixCore.h
)
