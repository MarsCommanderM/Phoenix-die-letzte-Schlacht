cmake_minimum_required(VERSION 3.22)

# PhoenixNetworking build targets.
#
# Two targets, following the engine's gem layout:
#   PhoenixNetworking.Static  static library holding the gem's implementation, which
#                 other gems and the project link against.
#   PhoenixNetworking         the loadable module O3DE activates at runtime; it carries
#                 only the module entry point and links the static library.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixNetworking/gem.json. scripts/validate.py fails if
# the two stop agreeing.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME PhoenixNetworking.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixnetworking_api_files.cmake
        phoenixnetworking_private_files.cmake
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
            Gem::PhoenixCharacter.Static
            Gem::PhoenixWorld.Static
)

ly_add_target(
    NAME PhoenixNetworking ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixnetworking_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::PhoenixNetworking.Static
)

# O3DE resolves gems per launcher role. This gem behaves identically in all
# three, so each alias points at the same module.
ly_create_alias(NAME PhoenixNetworking.Clients NAMESPACE Gem TARGETS Gem::PhoenixNetworking)
ly_create_alias(NAME PhoenixNetworking.Servers NAMESPACE Gem TARGETS Gem::PhoenixNetworking)
ly_create_alias(NAME PhoenixNetworking.Unified NAMESPACE Gem TARGETS Gem::PhoenixNetworking)
