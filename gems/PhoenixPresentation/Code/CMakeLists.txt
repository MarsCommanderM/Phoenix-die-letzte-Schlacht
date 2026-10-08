cmake_minimum_required(VERSION 3.22)

# PhoenixPresentation build targets.
#
# Two targets, following the engine's gem layout:
#   PhoenixPresentation.Static  static library holding the gem's implementation, which
#                 other gems and the project link against.
#   PhoenixPresentation         the loadable module O3DE activates at runtime; it carries
#                 only the module entry point and links the static library.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixPresentation/gem.json. scripts/validate.py fails if
# the two stop agreeing.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME PhoenixPresentation.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixpresentation_api_files.cmake
        phoenixpresentation_private_files.cmake
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
    NAME PhoenixPresentation ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixpresentation_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::PhoenixPresentation.Static
)

# O3DE resolves gems per launcher role. This gem behaves identically in all
# three, so each alias points at the same module.
ly_create_alias(NAME PhoenixPresentation.Clients NAMESPACE Gem TARGETS Gem::PhoenixPresentation)
ly_create_alias(NAME PhoenixPresentation.Servers NAMESPACE Gem TARGETS Gem::PhoenixPresentation)
ly_create_alias(NAME PhoenixPresentation.Unified NAMESPACE Gem TARGETS Gem::PhoenixPresentation)
