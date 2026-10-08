# PhoenixCharacter build targets.
#
# Three targets, following the engine's gem pattern:
#   PhoenixCharacter.API            INTERFACE; the public headers dependent gems consume.
#   PhoenixCharacter.Private.Object STATIC; the implementation. Private to this file.
#   PhoenixCharacter                the loadable module O3DE activates at runtime.
#
# BUILD_DEPENDENCIES mirror gems/PhoenixCharacter/gem.json. scripts/validate.py fails if
# the two stop agreeing.

# Resolve the platform abstraction layer directory for this folder. This may be
# a restricted platform, in which case o3de_pal_dir finds it elsewhere.
o3de_pal_dir(pal_dir ${CMAKE_CURRENT_LIST_DIR}/Platform/${PAL_PLATFORM_NAME} "${gem_restricted_path}" "${gem_path}" "${gem_parent_relative_path}")

# Platform traits (PAL_TRAIT_* defines) for this platform.
include(${pal_dir}/PAL_${PAL_PLATFORM_NAME_LOWERCASE}.cmake)

ly_add_target(
    NAME ${gem_name}.API INTERFACE
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcharacter_api_files.cmake
        ${pal_dir}/phoenixcharacter_api_files.cmake
    INCLUDE_DIRECTORIES
        INTERFACE
            Include
    BUILD_DEPENDENCIES
        INTERFACE
            AZ::AzCore
            Gem::PhoenixCore.API
            Gem::PhoenixGameplay.API
)

# Internal target. Not for use outside this file.
ly_add_target(
    NAME ${gem_name}.Private.Object STATIC
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcharacter_private_files.cmake
        ${pal_dir}/phoenixcharacter_private_files.cmake
    TARGET_PROPERTIES
        O3DE_PRIVATE_TARGET TRUE
    INCLUDE_DIRECTORIES
        PRIVATE
            Include
            Source
    BUILD_DEPENDENCIES
        PUBLIC
            AZ::AzCore
            AZ::AzFramework
            Gem::PhoenixCore.API
            Gem::PhoenixGameplay.API
)

ly_add_target(
    NAME ${gem_name} ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}
    NAMESPACE Gem
    FILES_CMAKE
        phoenixcharacter_shared_files.cmake
        ${pal_dir}/phoenixcharacter_shared_files.cmake
    INCLUDE_DIRECTORIES
        PUBLIC
            Include
        PRIVATE
            Source
    BUILD_DEPENDENCIES
        PUBLIC
            Gem::${gem_name}.API
        PRIVATE
            Gem::${gem_name}.Private.Object
)

# Make the gem name and version available to the module source.
ly_add_source_properties(
    SOURCES
        Source/PhoenixCharacterModule.cpp
    PROPERTY COMPILE_DEFINITIONS
        VALUES
            O3DE_GEM_NAME=${gem_name}
            O3DE_GEM_VERSION=${gem_version})

# This gem behaves identically in all launcher roles.
ly_create_alias(NAME ${gem_name}.Clients NAMESPACE Gem TARGETS Gem::${gem_name})
ly_create_alias(NAME ${gem_name}.Servers NAMESPACE Gem TARGETS Gem::${gem_name})
ly_create_alias(NAME ${gem_name}.Unified NAMESPACE Gem TARGETS Gem::${gem_name})

ly_create_alias(NAME ${gem_name}.Clients.API NAMESPACE Gem TARGETS Gem::${gem_name}.API)
ly_create_alias(NAME ${gem_name}.Servers.API NAMESPACE Gem TARGETS Gem::${gem_name}.API)
ly_create_alias(NAME ${gem_name}.Unified.API NAMESPACE Gem TARGETS Gem::${gem_name}.API)
