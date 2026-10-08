cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixPresentation)

set(FILES
    Code/Source/PhoenixPresentationModule.cpp
    Code/Source/PhoenixPresentationSystemComponent.cpp
    Code/Include/Phoenix/PhoenixPresentation/PhoenixPresentation.h
    Code/Include/Phoenix/Presentation/PhoenixPresentationEvent.h
    Code/Include/Phoenix/Presentation/PhoenixPresentationSystemComponent.h
)
