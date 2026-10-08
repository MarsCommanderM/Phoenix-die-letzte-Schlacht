"""Verify the independently versioned Phoenix contracts against each other and the code.

docs/tdd/06-data-schemas.md keeps product version, network protocol and save
schema on separate version lines, and the quality gates forbid an unversioned
change to any of them. Declaring three numbers in three files is the easy
half; this gate is the half that keeps them honest.

The defect it exists to prevent: a declared version the code cannot deliver.
A save_schema.json that claims `current: 3` while the migration chain in
tools/migration/migrate_save.py tops out at 2 is worse than having no config
at all, because every reader downstream — a launcher, a cloud-save service, a
support engineer reading a bug report — now trusts a number that is wrong. The
same applies to a compatibility window that excludes the build announcing it,
and to a readable save range with no migration behind part of it.

The code is the source of truth and the config must agree with it, so the save
checks import migrate_save rather than re-parsing its source: a check that
greps for `CURRENT_SCHEMA_VERSION = 2` passes on a line that was commented out.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "migration"))

import migrate_save  # noqa: E402
from _repo import load_json  # noqa: E402

CONFIG_DIR = ROOT / "project" / "Config"

VERSION_FILE = "version.json"
PROTOCOL_FILE = "network_protocol.json"
SAVE_FILE = "save_schema.json"

#: The integer fields each contract file must declare. Absent or wrongly typed,
#: the comparisons below are meaningless, so these are checked first.
REQUIRED_INTEGER_FIELDS = {
    VERSION_FILE: ("major", "minor", "patch"),
    PROTOCOL_FILE: ("protocol", "minimumCompatible", "maximumCompatible"),
    SAVE_FILE: ("current", "minimumReadable"),
}


def label(path: Path) -> str:
    """Repo-relative path where possible, absolute otherwise.

    --config-dir may point outside the repository (the tests validate throwaway
    directories), and relative_to raises rather than coping with that.
    """
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_integer(value) -> bool:
    """True for a JSON integer.

    bool is spelled out because it subclasses int: without this, `"protocol":
    true` would be accepted as an integer and then compared as 1.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def has_integers(document: dict, fields: tuple[str, ...]) -> bool:
    return all(is_integer(document.get(field)) for field in fields)


def validate(config_dir: Path) -> tuple[list[str], dict[str, dict]]:
    """Return (problems, the documents that parsed) for one config directory."""
    errors: list[str] = []
    documents: dict[str, dict] = {}

    for name, fields in REQUIRED_INTEGER_FIELDS.items():
        path = config_dir / name
        if not path.is_file():
            errors.append(
                f"{label(path)}: missing; the contract it declares would be unversioned"
            )
            continue
        try:
            document = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{label(path)}: invalid JSON: {exc}")
            continue
        if not isinstance(document, dict):
            errors.append(f"{label(path)}: top level must be a JSON object")
            continue

        documents[name] = document
        for field in fields:
            if not is_integer(document.get(field)):
                errors.append(
                    f"{label(path)}: field '{field}' must be an integer, got "
                    f"{document.get(field)!r}"
                )

    version = documents.get(VERSION_FILE)
    if version is not None and not (
        isinstance(version.get("product"), str) and version["product"].strip()
    ):
        errors.append(
            f"{label(config_dir / VERSION_FILE)}: field 'product' must be a "
            f"non-empty string, got {version.get('product')!r}"
        )

    protocol = documents.get(PROTOCOL_FILE)
    if protocol is not None and has_integers(
        protocol, REQUIRED_INTEGER_FIELDS[PROTOCOL_FILE]
    ):
        low = protocol["minimumCompatible"]
        speaks = protocol["protocol"]
        high = protocol["maximumCompatible"]
        if not low <= speaks <= high:
            errors.append(
                f"{label(config_dir / PROTOCOL_FILE)}: minimumCompatible <= protocol "
                f"<= maximumCompatible is violated ({low} <= {speaks} <= {high}); a "
                "build cannot advertise a compatibility window that excludes itself"
            )

    save = documents.get(SAVE_FILE)
    if save is not None and has_integers(save, REQUIRED_INTEGER_FIELDS[SAVE_FILE]):
        current = save["current"]
        minimum = save["minimumReadable"]
        where = label(config_dir / SAVE_FILE)

        if minimum > current:
            errors.append(
                f"{where}: minimumReadable ({minimum}) is above current ({current}); "
                "the build cannot read saves newer than the one it writes"
            )

        if current != migrate_save.CURRENT_SCHEMA_VERSION:
            errors.append(
                f"{where}: current is {current}, but tools/migration/migrate_save.py "
                f"writes version {migrate_save.CURRENT_SCHEMA_VERSION}; a config "
                "claiming a version the migration chain cannot produce is worse than "
                "no config"
            )

        for version_from in range(minimum, current):
            if version_from not in migrate_save.MIGRATIONS:
                errors.append(
                    f"{where}: minimumReadable is {minimum}, but no migration from "
                    f"v{version_from} is registered in migrate_save.MIGRATIONS; the "
                    "declared readable range is not actually reachable"
                )

    return errors, documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=CONFIG_DIR,
        help="validate a candidate config directory instead of project/Config",
    )
    args = parser.parse_args()

    errors, documents = validate(args.config_dir)

    if errors:
        print(
            f"Version contract validation FAILED ({len(errors)} problems):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    version = documents[VERSION_FILE]
    protocol = documents[PROTOCOL_FILE]
    save = documents[SAVE_FILE]
    fields = sum(len(f) for f in REQUIRED_INTEGER_FIELDS.values())
    steps = save["current"] - save["minimumReadable"]

    print(
        f"Version contract validation passed ({len(documents)} contract files, "
        f"{fields} integer fields checked): {version['product']} "
        f"{version['major']}.{version['minor']}.{version['patch']}, protocol "
        f"{protocol['protocol']} accepting {protocol['minimumCompatible']}-"
        f"{protocol['maximumCompatible']}, save v{save['minimumReadable']} to "
        f"v{save['current']} reachable through {steps} registered "
        f"migration{'' if steps == 1 else 's'}."
    )


if __name__ == "__main__":
    main()
