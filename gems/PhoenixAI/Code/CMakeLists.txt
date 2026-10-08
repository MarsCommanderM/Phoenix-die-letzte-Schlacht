cmake_minimum_required(VERSION 3.22)

# PhoenixAI build targets.
#
# Two targets, following the engine's gem layout:
#   PhoenixAI.Static  static library holding the gem's implementation, which
#                 other gems and the project link against.
#   PhoenixAI         the loadable module O3DE activates at runtime; it carries
#                 only the module entry point and links the static library.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixAI/gem.json. scripts/validate.py fails if
# the two stop agreeing.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME PhoenixAI.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixai_api_files.cmake
        phoenixai_private_files.cmake
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
)

ly_add_target(
    NAME PhoenixAI ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixai_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::PhoenixAI.Static
)

# O3DE resolves gems per launcher role. This gem behaves identically in all
# three, so each alias points at the same module.
ly_create_alias(NAME PhoenixAI.Clients NAMESPACE Gem TARGETS Gem::PhoenixAI)
ly_create_alias(NAME PhoenixAI.Servers NAMESPACE Gem TARGETS Gem::PhoenixAI)
ly_create_alias(NAME PhoenixAI.Unified NAMESPACE Gem TARGETS Gem::PhoenixAI)
