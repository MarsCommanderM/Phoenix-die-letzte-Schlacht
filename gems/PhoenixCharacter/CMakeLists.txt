cmake_minimum_required(VERSION 3.22)

# Phoenix gem file list.
#
# O3DE supplies the build functions; this file only declares the gem name and
# its translation units + public headers, following the engine's
# *_files.cmake convention where FILES carries both.

set(PHOENIX_GEM_NAME PhoenixCharacter)

set(FILES
    Code/Source/PhoenixCharacterModule.cpp
    Code/Source/PhoenixCharacterSystemComponent.cpp
    Code/Source/PhoenixMovementComponent.cpp
    Code/Include/Phoenix/Character/PhoenixCharacterSystemComponent.h
    Code/Include/Phoenix/Character/PhoenixMovementComponent.h
    Code/Include/Phoenix/Character/PhoenixMovementTypes.h
    Code/Include/Phoenix/PhoenixCharacter/PhoenixCharacter.h
)
