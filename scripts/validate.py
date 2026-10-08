"""Static validation gate for the Phoenix repository.

The imported starter only checked that each schema file was parseable JSON,
which left the things most likely to drift unverified. This also validates
the sample asset data against its schema, resolves cross-document
references, and enforces the gem dependency direction that
CONTRIBUTING.md requires every change to preserve.
"""
from __future__ import annotations

import json
import re
import sys

import sys
from pathlib import Path

# Make the sibling _repo helper importable regardless of cwd or isolated mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import DATA_SCHEMA_MAP, ROOT, data_dir, gem_dirs, load_json, schema_dir

try:
    import jsonschema
except ImportError:
    jsonschema = None

#: Declared layering. A gem may depend on gems in strictly lower tiers and,
#: within the peer tier, only on the gems named in PEER_EDGES.
TIERS = {
    "PhoenixCore": 0,
    "PhoenixGameplay": 1,
    "PhoenixCharacter": 2,
    "PhoenixWorld": 2,
    "PhoenixAI": 3,
    "PhoenixNetworking": 3,
    "PhoenixPresentation": 3,
    "PhoenixTools": 3,
}

PHOENIX_GEMS = frozenset(TIERS)


def check_schemas(errors: list[str]) -> dict[str, dict]:
    schemas: dict[str, dict] = {}
    files = sorted(schema_dir().glob("*.schema.json"))
    if not files:
        errors.append("no schema files found")
        return schemas

    for path in files:
        try:
            schemas[path.name] = load_json(path)
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
            continue
        if jsonschema is not None:
            try:
                jsonschema.Draft202012Validator.check_schema(schemas[path.name])
            except jsonschema.exceptions.SchemaError as exc:
                errors.append(f"{path.relative_to(ROOT)}: invalid schema: {exc.message}")
    return schemas


def check_data(schemas: dict[str, dict], errors: list[str]) -> dict[str, set[str]]:
    """Validate each data document and collect declared ids per category."""
    ids: dict[str, set[str]] = {category: set() for category in DATA_SCHEMA_MAP}

    for category, schema_name in DATA_SCHEMA_MAP.items():
        directory = data_dir() / category
        if not directory.is_dir():
            continue
        schema = schemas.get(schema_name)
        for path in sorted(directory.glob("*.json")):
            rel = path.relative_to(ROOT)
            try:
                document = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
                continue

            if isinstance(document, dict) and "id" in document:
                ids[category].add(document["id"])
                if path.stem != document["id"]:
                    errors.append(
                        f"{rel}: id '{document['id']}' does not match filename '{path.stem}'"
                    )

            if schema is None:
                errors.append(f"{rel}: governing schema {schema_name} is missing or invalid")
            elif jsonschema is not None:
                validator = jsonschema.Draft202012Validator(schema)
                for issue in sorted(validator.iter_errors(document), key=lambda e: e.path):
                    location = "/".join(str(p) for p in issue.path) or "(root)"
                    errors.append(f"{rel}: {location}: {issue.message}")
    return ids


def check_references(ids: dict[str, set[str]], errors: list[str]) -> None:
    """Missions must only reference objectives that exist."""
    directory = data_dir() / "Missions"
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.json")):
        try:
            document = load_json(path)
        except json.JSONDecodeError:
            continue  # already reported by check_data
        for objective in document.get("objectives", []):
            if objective not in ids.get("Objectives", set()):
                errors.append(
                    f"{path.relative_to(ROOT)}: references unknown objective '{objective}'"
                )


def check_gem_graph(errors: list[str]) -> None:
    """Enforce gem manifest consistency and the declared dependency direction."""
    dirs = gem_dirs()
    on_disk = {p.name for p in dirs}

    missing_tier = on_disk - PHOENIX_GEMS
    if missing_tier:
        errors.append(
            f"gems without a declared tier in scripts/validate.py: {sorted(missing_tier)}"
        )
    absent = PHOENIX_GEMS - on_disk
    if absent:
        errors.append(f"gems declared in TIERS but absent from gems/: {sorted(absent)}")

    project = load_json(ROOT / "project" / "project.json")
    declared = {entry.split("/")[-1] for entry in project.get("external_subdirectories", [])}
    if declared != on_disk:
        errors.append(
            "project.json external_subdirectories does not match gems/ on disk: "
            f"only in manifest {sorted(declared - on_disk)}, "
            f"only on disk {sorted(on_disk - declared)}"
        )

    for gem_dir in dirs:
        manifest = load_json(gem_dir / "gem.json")
        name = manifest.get("gem_name")
        if name != gem_dir.name:
            errors.append(
                f"gems/{gem_dir.name}/gem.json: gem_name '{name}' does not match directory"
            )
        if manifest.get("canonical_tags") != ["Gem"]:
            errors.append(f"gems/{gem_dir.name}/gem.json: canonical_tags must be ['Gem']")
        if manifest.get("type") != "Code":
            errors.append(f"gems/{gem_dir.name}/gem.json: type must be 'Code'")

        own_tier = TIERS.get(gem_dir.name)
        if own_tier is None:
            continue
        for dependency in manifest.get("dependencies", []):
            if dependency not in PHOENIX_GEMS:
                continue  # engine gem; ownership is O3DE's, not ours
            dep_tier = TIERS[dependency]
            if dep_tier >= own_tier:
                errors.append(
                    f"gems/{gem_dir.name}/gem.json: dependency on '{dependency}' "
                    f"(tier {dep_tier}) violates the direction for tier {own_tier}; "
                    "see docs/architecture/README.md"
                )


BUILD_DEP = re.compile(r"Gem::(\w+)\.Static")


def check_cmake_dependencies(errors: list[str]) -> None:
    """Assert each gem's CMake BUILD_DEPENDENCIES agree with its gem.json.

    docs/tdd/02-architecture.md states the build graph and the declared graph
    cannot drift apart. That is only true if something checks it.
    """
    for gem_dir in gem_dirs():
        cmake_file = gem_dir / "Code" / "CMakeLists.txt"
        if not cmake_file.is_file():
            errors.append(f"gems/{gem_dir.name}/Code/CMakeLists.txt: missing")
            continue

        manifest = load_json(gem_dir / "gem.json")
        declared = {d for d in manifest.get("dependencies", []) if d in PHOENIX_GEMS}
        in_cmake = set(BUILD_DEP.findall(cmake_file.read_text(encoding="utf-8")))
        in_cmake.discard(gem_dir.name)  # the module links its own .Static target

        if declared != in_cmake:
            only_manifest = sorted(declared - in_cmake)
            only_cmake = sorted(in_cmake - declared)
            errors.append(
                f"gems/{gem_dir.name}: CMake BUILD_DEPENDENCIES disagree with gem.json "
                f"(only in gem.json: {only_manifest}, only in CMake: {only_cmake})"
            )


def main() -> None:
    errors: list[str] = []

    if jsonschema is None:
        print(
            "WARNING: jsonschema is not installed; schema conformance is skipped.\n"
            "         Install it with: python -m pip install -r requirements-dev.txt",
            file=sys.stderr,
        )

    schemas = check_schemas(errors)
    ids = check_data(schemas, errors)
    check_references(ids, errors)
    check_gem_graph(errors)
    check_cmake_dependencies(errors)

    if errors:
        print(f"Phoenix static validation FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "Phoenix static validation passed "
        f"({len(schemas)} schemas, {sum(len(v) for v in ids.values())} data documents, "
        f"{len(gem_dirs())} gems)."
    )


if __name__ == "__main__":
    main()
