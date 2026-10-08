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

The product version cannot be imported -- it is a C++ header -- so it is
parsed, and the same hazard applies in full. The parser therefore strips `//`
and `/* */` comments before matching, because the whole point of the check is
to catch a header and a config that disagree, and a commented-out constant
that still satisfies the regex would report agreement with a line the compiler
never sees. Two places stating the product version is a drift waiting to
happen: a release where the launcher reports 0.2.0 and the binary reports
0.1.0 is a support call nobody can resolve, because both numbers are "the
version".

Shape is checked too, against project/Config/Schema/*.schema.json. The
relations above are what a schema cannot express; the schemas are what catch a
field that is missing, misspelled or of the wrong type before the relations
are evaluated on it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "migration"))

import migrate_save  # noqa: E402
from _repo import load_json  # noqa: E402

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without the dev deps
    jsonschema = None

CONFIG_DIR = ROOT / "project" / "Config"

VERSION_FILE = "version.json"
PROTOCOL_FILE = "network_protocol.json"
SAVE_FILE = "save_schema.json"

#: The header that declares the same product version to C++.
VERSION_HEADER = (
    ROOT / "gems" / "PhoenixCore" / "Code" / "Include" / "Phoenix" / "Core" / "PhoenixVersion.h"
)

#: config field -> C++ constant in Phoenix::Version.
VERSION_CONSTANTS = {"major": "Major", "minor": "Minor", "patch": "Patch"}

#: Shape schemas, one per contract file.
CONTRACT_SCHEMAS = {
    VERSION_FILE: "version.schema.json",
    PROTOCOL_FILE: "network_protocol.schema.json",
    SAVE_FILE: "save_schema.schema.json",
}

#: Matches /* ... */ and // ... so a commented-out constant cannot satisfy the
#: parse below. Without this the check would confirm agreement with a line the
#: compiler never compiles.
COMMENTS = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)

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


def check_shape(config_dir: Path, name: str, document: dict, errors: list[str]) -> None:
    """Validate one contract file against its JSON Schema.

    A skipped check must never read as a pass, so a missing jsonschema is an
    error here rather than a silent return.
    """
    if jsonschema is None:
        errors.append(
            "jsonschema is not installed, so contract shapes were not checked; "
            "install requirements-dev.txt"
        )
        return
    schema_path = config_dir / "Schema" / CONTRACT_SCHEMAS[name]
    if not schema_path.is_file():
        errors.append(
            f"{label(schema_path)}: missing; {name} would be shape-checked by nothing"
        )
        return
    try:
        schema = load_json(schema_path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label(schema_path)}: invalid JSON: {exc}")
        return
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        errors.append(f"{label(schema_path)}: not a valid JSON Schema: {exc.message}")
        return
    for problem in sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(document),
        key=lambda e: list(e.path),
    ):
        location = "/".join(str(part) for part in problem.path) or "(root)"
        errors.append(f"{label(config_dir / name)}: {location}: {problem.message}")


def parse_version_header(path: Path) -> tuple[dict[str, int], str | None, list[str]]:
    """Read Phoenix::Version from the header, ignoring anything commented out.

    Returns (constants, product, problems). A value that cannot be found is
    simply absent from the result: reporting "not declared" is correct, where
    defaulting it to 0 would manufacture an agreement.
    """
    problems: list[str] = []
    if not path.is_file():
        return {}, None, [f"{label(path)}: missing; the code has no product version"]

    source = COMMENTS.sub(" ", path.read_text(encoding="utf-8"))

    if not re.search(r"\bnamespace\s+Phoenix::Version\b", source):
        problems.append(
            f"{label(path)}: no 'namespace Phoenix::Version'; the constants below are "
            "then at some other scope and nothing here is the product version"
        )

    constants: dict[str, int] = {}
    for field, constant in VERSION_CONSTANTS.items():
        match = re.search(
            rf"\bconstexpr\s+unsigned\s+{constant}\s*=\s*(\d+)\s*;", source
        )
        if match is None:
            problems.append(
                f"{label(path)}: does not declare 'constexpr unsigned {constant}' "
                "outside a comment"
            )
            continue
        constants[field] = int(match.group(1))

    product_match = re.search(r'\bProduct\s*=\s*"([^"]*)"\s*;', source)
    product = product_match.group(1) if product_match else None
    if product is None:
        problems.append(f"{label(path)}: does not declare 'Product = \"...\"'")

    return constants, product, problems


def check_version_header(version: dict, errors: list[str]) -> None:
    """The config and the header must state the same product version."""
    constants, product, problems = parse_version_header(VERSION_HEADER)
    errors.extend(problems)

    for field, constant in VERSION_CONSTANTS.items():
        if field not in constants or not is_integer(version.get(field)):
            continue
        if constants[field] != version[field]:
            errors.append(
                f"{label(VERSION_HEADER)}: Phoenix::Version::{constant} is "
                f"{constants[field]}, but project/Config/{VERSION_FILE} declares "
                f"{field} {version[field]}. Both are 'the version', so a build that "
                "disagrees with its own config cannot be supported: bump them together"
            )

    declared_product = version.get("product")
    if product is not None and isinstance(declared_product, str) and product != declared_product:
        errors.append(
            f"{label(VERSION_HEADER)}: Phoenix::Version::Product is {product!r}, but "
            f"project/Config/{VERSION_FILE} declares product {declared_product!r}"
        )


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
        check_shape(config_dir, name, document, errors)
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

    if version is not None:
        # Only meaningful against project/Config; a throwaway --config-dir has
        # no header of its own, and the committed header is still the one the
        # code compiles, so it is compared either way.
        check_version_header(version, errors)

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
        f"Version contract validation passed ({len(documents)} contract files "
        f"shape-checked against their schemas, {fields} integer fields checked, "
        f"product version cross-checked against {VERSION_HEADER.name}): "
        f"{version['product']} "
        f"{version['major']}.{version['minor']}.{version['patch']}, protocol "
        f"{protocol['protocol']} accepting {protocol['minimumCompatible']}-"
        f"{protocol['maximumCompatible']}, save v{save['minimumReadable']} to "
        f"v{save['current']} reachable through {steps} registered "
        f"migration{'' if steps == 1 else 's'}."
    )


if __name__ == "__main__":
    main()
