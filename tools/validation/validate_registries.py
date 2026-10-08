"""Validate the two central registries: gameplay tags and physics collision layers.

docs/tdd/90-source-reconciliation.md C15 records that the architecture
depended on both of these before either existed. Creating the two JSON files
is the easy half. This is the half that makes them worth having, because both
registries exist to turn a silent runtime failure into a loud build failure,
and each has a specific one behind it.

**Tags.** The registry replaces free string comparison. A free string typo
(`"Charater.Player"`) compares unequal and the branch simply never runs: no
crash, no log, a feature that quietly does nothing. So the rule enforced here
is that a tag's namespace must be *declared*. Without that rule a typo in the
first segment would be accepted as a brand-new namespace, and the registry
would document the typo instead of rejecting it.

**Layers.** The engine's own behaviour is the reason. At O3DE tag 2605.0,
`AzPhysics::CollisionLayers::GetLayer(name)` returns
`CollisionLayer::Default` when the name is not found, and the
`CollisionLayer(const AZStd::string&)` constructor goes through it
(Code/Framework/AzFramework/AzFramework/Physics/Collision/CollisionLayers.h,
and .cpp line 42). A misspelled layer name therefore does not fail — it puts
the collider on layer 0. That is why index 0 must be `Default`, must be
marked reserved, and must collide with nothing: a collider that lands there
by accident then falls through the world, which someone notices, instead of
colliding with everything, which looks almost right.

The matrix checks are the other half. An asymmetric matrix (A collides with
B, B does not collide with A) is not a physics configuration, it is a
contradiction, and an incomplete one leaves a pair to the engine default. Both
are invisible in play until something passes through something else.

Neither registry's rules can be expressed in JSON Schema: every one of them is
a relation between entries. The schemas in project/Config/Schema/ carry the
shape; this carries the meaning.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from _repo import load_json  # noqa: E402

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without the dev deps
    jsonschema = None

CONFIG_DIR = ROOT / "project" / "Config"

TAGS_FILE = Path("Gameplay") / "tags.json"
LAYERS_FILE = Path("Physics") / "layers.json"

SCHEMAS = {
    TAGS_FILE: "tags.schema.json",
    LAYERS_FILE: "layers.schema.json",
}

#: The index AzPhysics reserves, and the name it reserves it under.
RESERVED_INDEX = 0
RESERVED_LAYER = "Default"


def label(path: Path) -> str:
    """Repo-relative where possible; --config-dir may point outside the tree."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load(path: Path, errors: list[str]) -> dict | None:
    if not path.is_file():
        errors.append(f"{label(path)}: missing; the registry it holds would be undefined")
        return None
    try:
        document = load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"{label(path)}: invalid JSON: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append(f"{label(path)}: top level must be a JSON object")
        return None
    return document


def check_against_schema(config_dir: Path, relative: Path, document: dict, errors: list[str]) -> None:
    """Shape check. Skipped loudly, never silently, when jsonschema is absent."""
    if jsonschema is None:
        errors.append(
            "jsonschema is not installed, so the registry shape was not checked; "
            "install requirements-dev.txt (a skipped check must not read as a pass)"
        )
        return
    schema_path = config_dir / "Schema" / SCHEMAS[relative]
    schema = load(schema_path, errors)
    if schema is None:
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
        errors.append(f"{label(config_dir / relative)}: {location}: {problem.message}")


def check_tags(config_dir: Path, errors: list[str]) -> dict | None:
    path = config_dir / TAGS_FILE
    document = load(path, errors)
    if document is None:
        return None
    check_against_schema(config_dir, TAGS_FILE, document, errors)

    where = label(path)
    namespaces = document.get("namespaces")
    tags = document.get("tags")
    if not isinstance(namespaces, list) or not isinstance(tags, list):
        return document  # the schema check above already reported the shape

    declared: list[str] = []
    for entry in namespaces:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            declared.append(entry["name"])

    duplicates = sorted({n for n in declared if declared.count(n) > 1})
    if duplicates:
        errors.append(f"{where}: namespace declared more than once: {', '.join(duplicates)}")
    if declared != sorted(declared):
        errors.append(
            f"{where}: namespaces are not in alphabetical order; sorted order keeps an "
            "insertion a one-line diff instead of an append nobody reviews in place"
        )

    declared_set = set(declared)
    names: list[str] = []
    used: set[str] = set()
    for entry in tags:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            continue
        name = entry["name"]
        names.append(name)
        namespace = name.split(".", 1)[0]
        used.add(namespace)
        if namespace not in declared_set:
            errors.append(
                f"{where}: tag '{name}' uses namespace '{namespace}', which is not "
                "declared. Declare it deliberately or correct the spelling: an "
                "undeclared namespace is how a typo becomes a registry entry"
            )
        if name in declared_set:
            errors.append(
                f"{where}: '{name}' is both a namespace and a tag; a namespace is a "
                "category, not a value"
            )

    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        errors.append(f"{where}: tag declared more than once: {', '.join(duplicates)}")
    if names != sorted(names):
        errors.append(f"{where}: tags are not in alphabetical order")

    for namespace in sorted(declared_set - used):
        errors.append(
            f"{where}: namespace '{namespace}' is declared but no tag uses it; either "
            "it is a leftover or the tag that was meant to use it is misspelled"
        )

    return document


def check_layers(config_dir: Path, errors: list[str]) -> dict | None:
    path = config_dir / LAYERS_FILE
    document = load(path, errors)
    if document is None:
        return None
    check_against_schema(config_dir, LAYERS_FILE, document, errors)

    where = label(path)
    layers = document.get("layers")
    collides = document.get("collidesWith")
    if not isinstance(layers, list) or not isinstance(collides, dict):
        return document

    names: list[str] = []
    indices: list[int] = []
    reserved_by_name: dict[str, bool] = {}
    for entry in layers:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        index = entry.get("index")
        if isinstance(name, str):
            names.append(name)
            reserved_by_name[name] = bool(entry.get("reserved"))
        if isinstance(index, int) and not isinstance(index, bool):
            indices.append(index)

    maximum = document.get("maxLayers")
    if isinstance(maximum, int) and len(names) > maximum:
        errors.append(
            f"{where}: {len(names)} layers declared but the engine supports {maximum}"
        )

    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        errors.append(f"{where}: layer declared more than once: {', '.join(duplicates)}")

    if sorted(indices) != list(range(len(indices))):
        errors.append(
            f"{where}: layer indices must be unique and contiguous from 0, got "
            f"{sorted(indices)}. A gap is a layer somebody deleted without renumbering, "
            "and the index is what the engine stores"
        )

    by_index = {
        entry["index"]: entry["name"]
        for entry in layers
        if isinstance(entry, dict)
        and isinstance(entry.get("index"), int)
        and isinstance(entry.get("name"), str)
    }
    if by_index.get(RESERVED_INDEX) != RESERVED_LAYER:
        errors.append(
            f"{where}: index {RESERVED_INDEX} must be '{RESERVED_LAYER}', because "
            "AzPhysics::CollisionLayer::Default is index 0 and an unresolved layer name "
            f"lands there; found {by_index.get(RESERVED_INDEX)!r}"
        )
    elif not reserved_by_name.get(RESERVED_LAYER):
        errors.append(
            f"{where}: '{RESERVED_LAYER}' must be marked reserved; it is the engine's "
            "fallback, not a layer Phoenix content may be authored onto"
        )

    declared = set(names)
    missing = sorted(declared - set(collides))
    if missing:
        errors.append(
            f"{where}: collidesWith does not name {', '.join(missing)}; an omitted "
            "layer leaves its collisions to the engine default, which is invisible "
            "until something passes through something else"
        )
    unknown = sorted(set(collides) - declared)
    if unknown:
        errors.append(f"{where}: collidesWith names undeclared layer(s): {', '.join(unknown)}")

    keys = list(collides)
    if keys != sorted(keys):
        errors.append(f"{where}: collidesWith keys are not in alphabetical order")

    for name, partners in collides.items():
        if not isinstance(partners, list):
            continue
        if partners != sorted(partners):
            errors.append(f"{where}: collidesWith['{name}'] is not in alphabetical order")
        for partner in partners:
            if not isinstance(partner, str):
                continue
            if partner not in declared:
                errors.append(
                    f"{where}: collidesWith['{name}'] names undeclared layer '{partner}'"
                )
                continue
            back = collides.get(partner)
            if not isinstance(back, list) or name not in back:
                errors.append(
                    f"{where}: collision matrix is asymmetric: '{name}' collides with "
                    f"'{partner}' but '{partner}' does not collide with '{name}'. "
                    "Collision is mutual; one direction alone is a contradiction the "
                    "engine resolves by dropping the collision"
                )

    inert = collides.get(RESERVED_LAYER)
    if isinstance(inert, list) and inert:
        errors.append(
            f"{where}: '{RESERVED_LAYER}' must collide with nothing. It is where a "
            "misspelled layer name lands, and a collider that falls through the world "
            "gets reported, where one that collides with everything looks almost right"
        )

    return document


def validate(config_dir: Path) -> tuple[list[str], dict[str, dict | None]]:
    errors: list[str] = []
    documents = {
        "tags": check_tags(config_dir, errors),
        "layers": check_layers(config_dir, errors),
    }
    return errors, documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=CONFIG_DIR,
        help="validate a candidate config directory instead of project/Config",
    )
    args = parser.parse_args()

    errors, documents = validate(args.config_dir)

    if errors:
        print(f"Registry validation FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    tags = documents["tags"] or {}
    layers = documents["layers"] or {}
    pairs = sum(len(v) for v in layers.get("collidesWith", {}).values()) // 2

    print(
        "Registry validation passed: "
        f"{len(tags.get('tags', []))} tags across "
        f"{len(tags.get('namespaces', []))} declared namespaces (v{tags.get('version')}), "
        f"{len(layers.get('layers', []))} collision layers with {pairs} symmetric "
        f"colliding pairs (v{layers.get('version')})."
    )


if __name__ == "__main__":
    main()
