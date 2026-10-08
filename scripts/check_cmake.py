"""Verify the Phoenix CMake structure without a registered O3DE engine.

Two kinds of file are checked:

*_files.cmake  pure `set(FILES ...)` lists. Every declared path must exist.
CMakeLists.txt target declarations. These call engine functions
               (ly_add_target, ly_create_alias, o3de_initialize) that a bare
               cmake does not provide, so they are configured against stubs.
               The ly_add_target stub additionally asserts that every
               FILES_CMAKE and PLATFORM_INCLUDE_FILES path it is handed
               exists, which makes this a structural check and not only a
               syntax check.

What this cannot do is link against O3DE: no engine is present. A green run
means the build structure is well formed, not that the game compiles.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import ROOT, gem_dirs

FILE_ENTRY = re.compile(r"^\s{4}(\S+\.(?:cpp|h|xml))\s*$", re.M)

# A fake o3de package config, so `find_package(o3de REQUIRED)` resolves and the
# engine API is available as no-ops that still validate their arguments.
O3DE_CONFIG = """
set(o3de_FOUND TRUE)

# Establishes the variables a gem's Code/CMakeLists.txt expects. The real
# function also resolves restricted platforms; the check does not need that.
function(o3de_gem_setup name)
    set(gem_name "${name}" PARENT_SCOPE)
    set(gem_version "0.1.0" PARENT_SCOPE)
    set(gem_path "${PHOENIX_CHECK_DIR}" PARENT_SCOPE)
    set(gem_restricted_path "" PARENT_SCOPE)
    set(gem_parent_relative_path "" PARENT_SCOPE)
endfunction()

# Five-argument form, as the engine defines it.
function(o3de_pal_dir out_var requested restricted_path gem_path parent_relative)
    if(NOT EXISTS "${requested}")
        message(FATAL_ERROR "o3de_pal_dir: no platform directory at ${requested}")
    endif()
    set(${out_var} "${requested}" PARENT_SCOPE)
endfunction()

function(ly_add_target)
    set(mode "")
    foreach(arg IN LISTS ARGN)
        if(arg STREQUAL "FILES_CMAKE" OR arg STREQUAL "PLATFORM_INCLUDE_FILES")
            set(mode "${arg}")
        elseif(arg MATCHES "^(NAME|NAMESPACE|INCLUDE_DIRECTORIES|BUILD_DEPENDENCIES|RUNTIME_DEPENDENCIES|COMPILE_DEFINITIONS|AUTOGEN_RULES|TARGET_PROPERTIES)$")
            set(mode "")
        elseif(mode)
            set(candidate "${arg}")
            if(NOT IS_ABSOLUTE "${candidate}")
                set(candidate "${PHOENIX_CHECK_DIR}/${arg}")
            endif()
            if(NOT EXISTS "${candidate}")
                message(FATAL_ERROR "${mode} references a missing file: ${arg}")
            endif()
        endif()
    endforeach()
endfunction()

# Verifies the named module source exists, which is the mistake this call
# would otherwise hide until link time.
function(ly_add_source_properties)
    set(expect_sources FALSE)
    foreach(arg IN LISTS ARGN)
        if(arg STREQUAL "SOURCES")
            set(expect_sources TRUE)
        elseif(arg MATCHES "^(PROPERTY|VALUES)$")
            set(expect_sources FALSE)
        elseif(expect_sources)
            if(NOT EXISTS "${PHOENIX_CHECK_DIR}/${arg}")
                message(FATAL_ERROR "ly_add_source_properties names a missing source: ${arg}")
            endif()
        endif()
    endforeach()
endfunction()

function(ly_create_alias)
endfunction()

function(o3de_initialize)
endfunction()
"""

HARNESS = """cmake_minimum_required(VERSION 3.22)
project(PhoenixCMakeStructureCheck LANGUAGES NONE)

# Values the engine would normally supply.
set(PAL_PLATFORM_NAME "Linux")
set(PAL_PLATFORM_NAME_LOWERCASE "linux")
set(PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE "MODULE")
set(PAL_TRAIT_BUILD_HOST_TOOLS TRUE)

set(PHOENIX_CHECK_DIR "{check_dir}")
set(gem_name "{gem_name}")
set(gem_version "0.1.0")
set(gem_path "{check_dir}")
set(gem_restricted_path "")
set(gem_parent_relative_path "")
list(APPEND CMAKE_PREFIX_PATH "{stub_dir}")

# The project entry point declares its own project() with C/CXX; the harness
# already established one, and re-declaring languages here would demand
# compilers this check does not need.
macro(project)
endmacro()

macro(add_subdirectory dir)
    if(NOT EXISTS "${{PHOENIX_CHECK_DIR}}/${{dir}}/CMakeLists.txt")
        message(FATAL_ERROR "add_subdirectory(${{dir}}) has no CMakeLists.txt")
    endif()
endmacro()

# Only the project entry point calls find_package(o3de); the gem and project
# Code/CMakeLists.txt files expect the engine API to be present already,
# because the engine established it further up its own build. Load the stubs
# directly so every file is checked under the same conditions.
include("{stub_config}")

include("{target}")
"""


def list_files() -> list[tuple[Path, Path]]:
    """(base directory for declared paths, *_files.cmake) pairs."""
    targets: list[tuple[Path, Path]] = []
    for gem in gem_dirs():
        code = gem / "Code"
        targets += [(code, p) for p in sorted(code.glob("*_files.cmake"))]
        targets += [
            (code, p) for p in sorted(code.glob("Platform/*/*_files.cmake"))
        ]
    code = ROOT / "project" / "Code"
    targets += [(code, p) for p in sorted(code.glob("*_files.cmake"))]
    targets += [
        (code, p) for p in sorted(code.glob("Platform/*/*_files.cmake"))
    ]
    return targets


def cmake_lists() -> list[Path]:
    """CMakeLists.txt files that declare targets or entry points."""
    out = []
    for gem in gem_dirs():
        out.append(gem / "CMakeLists.txt")
        out.append(gem / "Code" / "CMakeLists.txt")
    out.append(ROOT / "project" / "CMakeLists.txt")
    out.append(ROOT / "project" / "Code" / "CMakeLists.txt")
    return out


def check_declared_paths(errors: list[str]) -> int:
    checked = 0
    for base, cmake_file in list_files():
        if not cmake_file.is_file():
            errors.append(f"{cmake_file.relative_to(ROOT)}: missing")
            continue
        for match in FILE_ENTRY.finditer(cmake_file.read_text(encoding="utf-8")):
            checked += 1
            if not (base / match.group(1)).is_file():
                errors.append(
                    f"{cmake_file.relative_to(ROOT)}: declares missing file '{match.group(1)}'"
                )
    return checked


def check_configures(errors: list[str]) -> int:
    cmake = shutil.which("cmake")
    if cmake is None:
        print("NOTE: cmake not found; configure check skipped (path check still ran).")
        return 0

    configured = 0
    with tempfile.TemporaryDirectory() as tmp:
        stub_dir = Path(tmp) / "o3de-stub"
        stub_dir.mkdir()
        (stub_dir / "o3de-config.cmake").write_text(O3DE_CONFIG, encoding="utf-8")

        for index, target in enumerate(cmake_lists()):
            if not target.is_file():
                errors.append(f"{target.relative_to(ROOT)}: missing")
                continue

            work = Path(tmp) / f"case{index}"
            work.mkdir()
            (work / "CMakeLists.txt").write_text(
                HARNESS.format(
                    target=target.as_posix(),
                    check_dir=target.parent.as_posix(),
                    gem_name=(
                        target.parent.parent.name
                        if target.parent.name == "Code"
                        else target.parent.name
                    ),
                    stub_dir=stub_dir.as_posix(),
                    stub_config=(stub_dir / "o3de-config.cmake").as_posix(),
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [cmake, "-S", str(work), "-B", str(work / "b")],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                lines = [
                    line.strip()
                    for line in (result.stderr + "\n" + result.stdout).splitlines()
                    if line.strip() and "Configuring incomplete" not in line
                ]
                errors.append(
                    f"{target.relative_to(ROOT)}: {' '.join(lines[:3]) or 'configure failed'}"
                )
            else:
                configured += 1
    return configured


def main() -> None:
    errors: list[str] = []
    paths = check_declared_paths(errors)
    configured = check_configures(errors)

    if errors:
        print(f"CMake structure check FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"CMake structure check passed ({configured} CMakeLists configured, "
        f"{paths} declared paths exist)."
    )


if __name__ == "__main__":
    main()
