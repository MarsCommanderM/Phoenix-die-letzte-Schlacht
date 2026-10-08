cmake_minimum_required(VERSION 3.22)

# Phoenix project build targets.
#
# The project owns only its own code; every domain responsibility lives in a
# gem reached through project.json external_subdirectories. See
# docs/architecture/README.md for the dependency direction this preserves.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME Phoenix.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenix_api_files.cmake
        phoenix_private_files.cmake
    PLATFORM_INCLUDE_FILES
        ${pal_dir}/platform_${PAL_PLATFORM_NAME_LOWERCASE}_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PUBLIC
            AZ::AzCore
            AZ::AzFramework
            Gem::PhoenixCore.Static
            Gem::PhoenixGameplay.Static
)

ly_add_target(
    NAME Phoenix ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenix_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::Phoenix.Static
)

ly_create_alias(NAME Phoenix.Clients NAMESPACE Gem TARGETS Gem::Phoenix)
ly_create_alias(NAME Phoenix.Servers NAMESPACE Gem TARGETS Gem::Phoenix)
ly_create_alias(NAME Phoenix.Unified NAMESPACE Gem TARGETS Gem::Phoenix)

# AutoComponent XML under Source/AutoGen is compiled by O3DE Multiplayer into
# generated C++; the generated files are not committed.
include(${CMAKE_CURRENT_LIST_DIR}/Phoenix_autogen_files.cmake)
