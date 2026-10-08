"""Verify every Phoenix CMake file list parses and references real files.

The imported starter shipped eight gem CMakeLists in which the header list
was emitted as trailing arguments to an unterminated
cmake_minimum_required(), so `cmake` rejected all of them with "called with
unknown argument". That class of defect is invisible until someone
configures the project, so it is checked here.
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


def list_files() -> list[tuple[Path, Path]]:
    """(base directory, cmake list file) pairs covering the whole repository."""
    targets = [(gem, gem / "CMakeLists.txt") for gem in gem_dirs()]
    code = ROOT / "project" / "Code"
    targets.append((code, code / "Phoenix_files.cmake"))
    targets.append((code, code / "Phoenix_autogen_files.cmake"))
    targets.append((code, code / "CMakeLists.txt"))
    return targets


def check_paths(errors: list[str]) -> int:
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


def check_parses(errors: list[str]) -> int:
    """Configure each list file in isolation with the real cmake binary."""
    cmake = shutil.which("cmake")
    if cmake is None:
        print("NOTE: cmake not found; parse check skipped (path check still ran).")
        return 0

    parsed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for index, (_, cmake_file) in enumerate(list_files()):
            if not cmake_file.is_file():
                continue
            work = Path(tmp) / f"case{index}"
            work.mkdir()
            (work / "CMakeLists.txt").write_text(
                "cmake_minimum_required(VERSION 3.22)\n"
                "project(PhoenixCMakeParseCheck LANGUAGES NONE)\n"
                f'include("{cmake_file.as_posix()}")\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [cmake, "-S", str(work), "-B", str(work / "b")],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                # CMake reports the diagnostic itself on stderr and only the
                # "Configuring incomplete" summary on stdout, so read both and
                # keep the lines that name the cause.
                lines = [
                    line.strip()
                    for line in (result.stderr + "\n" + result.stdout).splitlines()
                    if line.strip() and "Configuring incomplete" not in line
                ]
                detail = " ".join(lines[:3]) if lines else "configure failed"
                errors.append(f"{cmake_file.relative_to(ROOT)}: {detail}")
            else:
                parsed += 1
    return parsed


def main() -> None:
    errors: list[str] = []
    checked = check_paths(errors)
    parsed = check_parses(errors)

    if errors:
        print(f"CMake check FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(f"CMake check passed ({parsed} list files parsed, {checked} declared paths exist).")


if __name__ == "__main__":
    main()
