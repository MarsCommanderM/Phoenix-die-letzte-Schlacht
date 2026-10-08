cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixGameplay)

set(FILES
    Code/Source/PhoenixGameplayModule.cpp
    Code/Source/PhoenixGameplaySystemComponent.cpp
    Code/Include/Phoenix/Gameplay/PhoenixAction.h
    Code/Include/Phoenix/Gameplay/PhoenixGameplayState.h
    Code/Include/Phoenix/Gameplay/PhoenixGameplaySystemComponent.h
    Code/Include/Phoenix/PhoenixGameplay/PhoenixGameplay.h
)
