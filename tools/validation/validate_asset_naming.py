"""Enforce the asset naming convention in docs/production/naming.md.

Master Baseline v5.1 section 231 asks for one naming convention. A convention
without a gate lasts about three weeks, and the cost of losing it is not
tidiness:

* O3DE resolves assets by path, and asset paths are case-sensitive on Linux
  and case-insensitive on Windows. A reference to `T_Rock_BC.png` against a
  file stored as `t_rock_bc.png` works on a developer's Windows machine and
  fails on the dedicated Linux server build -- the machine nobody watches,
  after review has already passed. So the case-collision check runs across
  the whole repository, not only the asset tree.
* A space or an accented character in a path survives the editor and then
  breaks command lines, .setreg entries and shader include paths.
* `_final`, `_v2`, `_old`, `_copy` are how a tree fills with files nobody
  dares delete. Version control is the version control.

Honesty about coverage. No production asset is authored yet, so the
production-prefix rules currently have nothing to run against. This tool
therefore reports the number of files it actually checked per category and
names the empty ones, because a validator that prints "passed" over an empty
directory has told you nothing and implied the opposite.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from _repo import DATA_SCHEMA_MAP, is_excluded, iter_source_files  # noqa: E402

#: Produced-asset prefixes, keyed by the extensions they govern. Kept in step
#: with the table in docs/production/naming.md by tests/Unit/test_asset_naming.py.
PRODUCTION_PREFIXES = {
    "T_": {".png", ".tga", ".tif", ".exr"},
    "M_": {".material"},
    "SM_": {".fbx"},
    "SK_": {".fbx"},
    "A_": {".fbx", ".motion"},
    "P_": {".prefab"},
    "S_": {".wav", ".ogg"},
    "L_": {".prefab"},
}

#: Extension to the prefixes that may introduce it. Several prefixes share
#: .fbx and .prefab, so the rule is "one of these", never "exactly this one".
PREFIXES_BY_EXTENSION: dict[str, set[str]] = defaultdict(set)
for _prefix, _extensions in PRODUCTION_PREFIXES.items():
    for _extension in _extensions:
        PREFIXES_BY_EXTENSION[_extension].add(_prefix)

#: Produced assets are PascalCase after the prefix, with _Suffix segments.
PRODUCTION_STEM = re.compile(r"^[A-Z][A-Za-z0-9]*(_[A-Z0-9][A-Za-z0-9]*)*$")

#: Data documents and their ids are lower_snake_case.
DATA_STEM = re.compile(r"^[a-z][a-z0-9_]*$")

#: Path characters that are allowed anywhere in the repository.
PATH_CHARACTERS = re.compile(r"^[A-Za-z0-9_.\-/]+$")

#: Version and status words that must not appear in a filename.
FORBIDDEN_SUFFIXES = (
    "_final",
    "_new",
    "_old",
    "_copy",
    "_wip",
    "_temp",
    "_tmp",
    "_bak",
    "_backup",
)

#: `_v2`, `_V10`: a numbered revision in a name.
FORBIDDEN_VERSION = re.compile(r"_[vV]\d+$")

#: Paths the naming rules deliberately do not reach. Dotfiles are tool
#: configuration whose names the tools choose; tests/ and scripts/ are Python,
#: whose convention is PEP 8 and whose gate is the test suite.
UNGOVERNED_PREFIXES = ("docs/", "scripts/", "tests/", "tools/", ".github/")


def singular(category: str) -> str:
    """'Actions' -> 'action'. Only the plural forms the data tree actually uses."""
    lowered = category.lower()
    return lowered[:-1] if lowered.endswith("s") else lowered


def governed(relative: Path) -> bool:
    text = relative.as_posix()
    if text.startswith(".") or "/." in text:
        return False
    return not text.startswith(UNGOVERNED_PREFIXES)


def check_case_collisions(errors: list[str]) -> int:
    """Two files differing only by case: works on Windows, breaks on Linux."""
    seen: dict[str, list[str]] = defaultdict(list)
    for path in iter_source_files():
        text = path.relative_to(ROOT).as_posix()
        seen[text.lower()].append(text)
    for lowered, paths in sorted(seen.items()):
        if len(paths) > 1:
            errors.append(
                "paths differ only by case: "
                + ", ".join(sorted(paths))
                + " -- this resolves on Windows and fails on the Linux server build"
            )
        del lowered
    return len(seen)


def check_path_characters(errors: list[str]) -> int:
    checked = 0
    for path in iter_source_files():
        relative = path.relative_to(ROOT)
        if not governed(relative):
            continue
        checked += 1
        text = relative.as_posix()
        if not PATH_CHARACTERS.match(text):
            errors.append(
                f"{text}: contains a character outside [A-Za-z0-9_.-/]; spaces and "
                "accented characters break command lines, .setreg entries and shader "
                "include paths"
            )
        stem = relative.stem
        for suffix in FORBIDDEN_SUFFIXES:
            if stem.lower().endswith(suffix):
                errors.append(
                    f"{text}: name ends in '{suffix}'; version control is the version "
                    "control, and these are the names a tree accumulates and nobody "
                    "dares delete"
                )
        if FORBIDDEN_VERSION.search(stem):
            errors.append(f"{text}: name carries a numbered revision; use git history")
    return checked


def check_data_documents(errors: list[str]) -> int:
    """Data documents are <singular-category>_<name>.json, lower_snake_case."""
    data = ROOT / "project" / "Assets" / "Data"
    if not data.is_dir():
        return 0
    checked = 0
    for category in sorted(p for p in data.iterdir() if p.is_dir()):
        prefix = f"{singular(category.name)}_"
        for path in sorted(category.glob("*.json")):
            checked += 1
            text = path.relative_to(ROOT).as_posix()
            stem = path.stem
            if not DATA_STEM.match(stem):
                errors.append(f"{text}: data document names are lower_snake_case")
            if not stem.startswith(prefix):
                errors.append(
                    f"{text}: must start with '{prefix}'. The prefix repeats the "
                    "directory on purpose: an id is quoted in logs, bug reports and "
                    "save files far from its directory"
                )
        if category.name not in DATA_SCHEMA_MAP:
            # validate_assets.py owns this rule; repeated here only so that a
            # category added without a schema cannot slip past both tools.
            errors.append(
                f"project/Assets/Data/{category.name}: no governing schema is mapped"
            )
    return checked


def check_production_assets(errors: list[str]) -> dict[str, int]:
    """Prefix and casing for produced assets, wherever they are in the tree."""
    counts: dict[str, int] = {prefix: 0 for prefix in PRODUCTION_PREFIXES}
    for path in iter_source_files():
        relative = path.relative_to(ROOT)
        if not governed(relative):
            continue
        extension = relative.suffix.lower()
        allowed = PREFIXES_BY_EXTENSION.get(extension)
        if not allowed:
            continue
        text = relative.as_posix()
        stem = relative.stem
        match = next((p for p in sorted(allowed, key=len, reverse=True) if stem.startswith(p)), None)
        if match is None:
            errors.append(
                f"{text}: a {extension} asset must start with one of "
                f"{', '.join(sorted(allowed))} (docs/production/naming.md)"
            )
            continue
        counts[match] += 1
        if not PRODUCTION_STEM.match(stem[len(match):]):
            errors.append(
                f"{text}: '{stem[len(match):]}' must be PascalCase with _Suffix "
                "segments, e.g. T_RockCliff_BaseColor"
            )
    return counts


def validate() -> tuple[list[str], dict[str, object]]:
    errors: list[str] = []
    stats: dict[str, object] = {
        "paths": check_case_collisions(errors),
        "governed": check_path_characters(errors),
        "data": check_data_documents(errors),
        "production": check_production_assets(errors),
    }
    return errors, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()

    errors, stats = validate()

    if errors:
        print(f"Asset naming FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    production: dict[str, int] = stats["production"]  # type: ignore[assignment]
    authored = sum(production.values())
    empty = sorted(prefix for prefix, count in production.items() if count == 0)

    print(
        f"Asset naming passed: {stats['paths']} paths checked for case collisions, "
        f"{stats['governed']} governed paths checked for characters and forbidden "
        f"suffixes, {stats['data']} data documents checked for prefix and case, "
        f"{authored} production assets checked."
    )
    if empty:
        # Stated, not implied. These rules are declared and currently have
        # nothing to run against; a bare "passed" would read as coverage.
        print(
            "  no assets authored yet for: "
            + ", ".join(empty)
            + " -- those rules are declared, not yet exercised"
        )


if __name__ == "__main__":
    main()
