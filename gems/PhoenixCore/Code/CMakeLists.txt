cmake_minimum_required(VERSION 3.22)

# PhoenixCore build targets.
#
# Two targets, following the engine's gem layout:
#   PhoenixCore.Static  static library holding the gem's implementation, which
#                 other gems and the project link against.
#   PhoenixCore         the loadable module O3DE activates at runtime; it carries
#                 only the module entry point and links the static library.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixCore/gem.json. scripts/validate.py fails if
# the two stop agreeing.

set(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME})

ly_add_target(
    NAME PhoenixCore.Static STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcore_api_files.cmake
        phoenixcore_private_files.cmake
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
)

ly_add_target(
    NAME PhoenixCore ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcore_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PRIVATE
            Gem::PhoenixCore.Static
)

# O3DE resolves gems per launcher role. This gem behaves identically in all
# three, so each alias points at the same module.
ly_create_alias(NAME PhoenixCore.Clients NAMESPACE Gem TARGETS Gem::PhoenixCore)
ly_create_alias(NAME PhoenixCore.Servers NAMESPACE Gem TARGETS Gem::PhoenixCore)
ly_create_alias(NAME PhoenixCore.Unified NAMESPACE Gem TARGETS Gem::PhoenixCore)
