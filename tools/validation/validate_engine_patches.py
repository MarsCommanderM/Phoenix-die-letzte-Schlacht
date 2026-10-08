"""Validate the engine patch register against the patch files on disk.

Master Baseline v5.1 sections 269-270 ask for an engine patch register.
ADR-0009 already sets the policy; the register is what makes its rule 3 --
"the patch set is reviewed at every engine upgrade" -- something a person can
actually execute, because a review needs a list.

The defect this prevents is specific and expensive. A carried engine patch
costs nothing on the day it lands and costs a rebase at every upgrade
afterwards. Left to prose, the patch set drifts out of the register in both
directions, and both are bad:

* A patch on disk with no row in the register is a liability nobody counts.
  It is discovered at upgrade time, which is the one moment when discovering
  it is useless, because the choice not to carry it has already expired.
* A row left behind after its patch was dropped makes the fork look more
  divergent than it is, and the next upgrade pays to re-verify a patch that
  does not exist.

So the register and the directory are compared in both directions, and every
field ADR-0009 requires is checked for being filled in rather than merely
present. `Upstream issue` in particular: an engine bug that was never
reported upstream is a patch with no exit condition, carried forever by
construction.

The register is currently empty, which is why the negative tests in
tests/Unit/test_engine_patches.py exist. A validator whose per-entry rules
have never run against an entry has not been shown to work.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PATCH_DIR = ROOT / "docs" / "engine-patches"
REGISTER = "README.md"
TEMPLATE = "TEMPLATE.md"

#: Required header fields, per the field reference in the register.
REQUIRED_FIELDS = (
    "Status",
    "Owner",
    "ADR",
    "Engine version",
    "Category",
    "Upstream issue",
    "Dropped in",
)

#: Required sections. Each one answers a question that decides whether the
#: patch should exist at all, so a patch missing one has not been argued.
REQUIRED_SECTIONS = (
    "What the patch changes",
    "Why this cannot live in a Phoenix gem",
    "Rebase cost",
    "Exit condition",
)

#: The five admissible reasons from ADR-0009. Anything else is a gameplay
#: shortcut wearing a different hat.
CATEGORIES = frozenset(
    {"engine-bug", "extension-point", "performance", "platform", "security"}
)

STATUSES = frozenset({"proposed", "carried", "dropped"})

#: Patch files are NNNN-slug.md, matching the ADR convention.
PATCH_NAME = re.compile(r"^(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.md$")

#: A register row: | [0001](0001-slug.md) | Title | category | owner | ver | status |
REGISTER_ROW = re.compile(r"^\|\s*\[?(\d{4})\]?\(?([^)|]*)\)?\s*\|(.+)\|\s*$")


def field(text: str, name: str) -> str | None:
    match = re.search(rf"^{re.escape(name)}:[ \t]*(.*)$", text, re.M)
    return match.group(1).strip() if match else None


def check_template(errors: list[str]) -> None:
    """The template must carry every field and section it asks patches for.

    Checked for presence, not for filled values: its values are placeholders
    by definition. Without this, the template could lose a field and every
    patch written from it afterwards would be missing it too.
    """
    path = PATCH_DIR / TEMPLATE
    if not path.is_file():
        errors.append(f"docs/engine-patches/{TEMPLATE}: missing")
        return
    text = path.read_text(encoding="utf-8")
    for name in REQUIRED_FIELDS:
        if field(text, name) is None:
            errors.append(f"docs/engine-patches/{TEMPLATE}: no '{name}:' field")
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in text:
            errors.append(f"docs/engine-patches/{TEMPLATE}: no '## {section}' section")


def patch_files() -> list[Path]:
    if not PATCH_DIR.is_dir():
        return []
    return sorted(
        p
        for p in PATCH_DIR.glob("*.md")
        if p.name not in {REGISTER, TEMPLATE}
    )


def check_patch(path: Path, errors: list[str]) -> dict[str, str]:
    where = f"docs/engine-patches/{path.name}"
    values: dict[str, str] = {}

    if not PATCH_NAME.match(path.name):
        errors.append(f"{where}: name must be NNNN-slug.md, lower-case and hyphenated")

    text = path.read_text(encoding="utf-8")

    for name in REQUIRED_FIELDS:
        value = field(text, name)
        if value is None:
            errors.append(f"{where}: no '{name}:' field")
            continue
        if not value:
            errors.append(
                f"{where}: '{name}' is empty. ADR-0009 requires it; an unfilled field "
                "is the same liability as a missing one, with the appearance of rigour"
            )
            continue
        values[name] = value

    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in text:
            errors.append(
                f"{where}: no '## {section}' section; that question decides whether "
                "the patch should exist"
            )

    status = values.get("Status")
    if status is not None and status not in STATUSES:
        errors.append(f"{where}: Status '{status}' is not one of {sorted(STATUSES)}")

    category = values.get("Category")
    if category is not None and category not in CATEGORIES:
        errors.append(
            f"{where}: Category '{category}' is not one of the five admissible reasons "
            f"in ADR-0009 ({', '.join(sorted(CATEGORIES))})"
        )

    upstream = values.get("Upstream issue")
    if upstream is not None and not (
        upstream.startswith(("http://", "https://")) or upstream.startswith("none - ")
    ):
        errors.append(
            f"{where}: Upstream issue must be a link or 'none - <where reported>'; got "
            f"{upstream!r}. An engine bug nobody reported upstream has no exit "
            "condition, so the patch is carried forever by construction"
        )

    adr = values.get("ADR")
    if adr is not None and not (PATCH_DIR / adr).resolve().is_file():
        errors.append(f"{where}: ADR '{adr}' does not resolve to a file")

    dropped = values.get("Dropped in")
    if status == "dropped" and dropped in (None, "n/a"):
        errors.append(
            f"{where}: Status is 'dropped' but 'Dropped in' is {dropped!r}; the engine "
            "version that ended the patch is the whole value of recording the drop"
        )
    if status != "dropped" and dropped not in (None, "n/a"):
        errors.append(
            f"{where}: 'Dropped in' is {dropped!r} but Status is {status!r}; a patch "
            "with a drop version is dropped"
        )

    return values


def register_rows(errors: list[str]) -> dict[str, str]:
    """The patch numbers the register's table claims, mapped to their row."""
    path = PATCH_DIR / REGISTER
    if not path.is_file():
        errors.append(f"docs/engine-patches/{REGISTER}: missing; the register is the list")
        return {}
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = REGISTER_ROW.match(line.strip())
        if match is None:
            continue
        rows[match.group(1)] = match.group(2) or ""
    return rows


def validate() -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    check_template(errors)

    files = patch_files()
    carried = 0
    numbers: dict[str, Path] = {}
    for path in files:
        values = check_patch(path, errors)
        if values.get("Status") == "carried":
            carried += 1
        match = PATCH_NAME.match(path.name)
        if match:
            number = match.group(1)
            if number in numbers:
                errors.append(
                    f"docs/engine-patches/{path.name}: number {number} is already used "
                    f"by {numbers[number].name}"
                )
            numbers[number] = path

    rows = register_rows(errors)

    # Both directions. Each one is a different way for the register to lie.
    for number in sorted(set(rows) - set(numbers)):
        errors.append(
            f"docs/engine-patches/{REGISTER}: the table lists patch {number}, which has "
            "no file. A row left behind after a drop makes the fork look more divergent "
            "than it is, and the next upgrade pays to re-verify nothing"
        )
    for number in sorted(set(numbers) - set(rows)):
        path = numbers[number]
        status = field(path.read_text(encoding="utf-8"), "Status")
        if status == "dropped":
            continue  # dropped patches keep their file and lose their row, by design
        errors.append(
            f"docs/engine-patches/{REGISTER}: patch {number} ({path.name}) is not in the "
            "table. A patch nobody counts is discovered at upgrade time, which is the "
            "one moment when discovering it is useless"
        )

    return errors, {"patches": len(files), "carried": carried, "rows": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.parse_args()

    errors, stats = validate()

    if errors:
        print(f"Engine patch register FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    if stats["patches"] == 0:
        print(
            "Engine patch register passed: no patches carried; the fork is identical to "
            "the pinned engine. Template and register structure checked."
        )
    else:
        print(
            f"Engine patch register passed: {stats['patches']} patch file(s), "
            f"{stats['carried']} carried, {stats['rows']} register row(s) in agreement."
        )


if __name__ == "__main__":
    main()
