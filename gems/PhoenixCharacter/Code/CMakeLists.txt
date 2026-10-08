cmake_minimum_required(VERSION 3.22)

# PhoenixCharacter build targets.
#
# Two targets, following the engine's gem layout:
#   PhoenixCharacter.Static  static library holding the gem's implementation, which
#                 other gems and the project link against.
#   PhoenixCharacter         the loadable module O3DE activates at runtime; it carries
#                 only the module entry point and links the static library.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixCharacter/gem.json. scripts/validate.py fails if
# the two stop agreeing.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME PhoenixCharacter.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcharacter_api_files.cmake
        phoenixcharacter_private_files.cmake
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
    NAME PhoenixCharacter ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcharacter_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::PhoenixCharacter.Static
)

# O3DE resolves gems per launcher role. This gem behaves identically in all
# three, so each alias points at the same module.
ly_create_alias(NAME PhoenixCharacter.Clients NAMESPACE Gem TARGETS Gem::PhoenixCharacter)
ly_create_alias(NAME PhoenixCharacter.Servers NAMESPACE Gem TARGETS Gem::PhoenixCharacter)
ly_create_alias(NAME PhoenixCharacter.Unified NAMESPACE Gem TARGETS Gem::PhoenixCharacter)
