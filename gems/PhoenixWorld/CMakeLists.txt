# Phoenix PhoenixWorld gem.
#
# o3de_gem_setup establishes gem_name, gem_path, gem_restricted_path and
# gem_parent_relative_path, which the Code/ CMakeLists needs for PAL
# resolution. Build targets are declared there.

o3de_gem_setup("PhoenixWorld")

add_subdirectory(Code)
