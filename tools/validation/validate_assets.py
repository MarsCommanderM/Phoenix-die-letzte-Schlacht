"""Validate Phoenix asset authoring data beyond schema validity.

scripts/validate.py checks that each document matches its schema. These are
the rules a schema cannot express: naming, orphans, schema coverage, and
whether a schema exists for every data category at all.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from _repo import DATA_SCHEMA_MAP, data_dir, load_json, schema_dir  # noqa: E402

#: Asset ids are lower_snake_case. A mixed convention makes every lookup a
#: guess and breaks case-sensitive asset paths between platforms.
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []
    documents = 0

    if not data_dir().is_dir():
        print("No asset data directory; nothing to validate.")
        return

    # Every data category must have a governing schema. A category without
    # one is unvalidated content that looks validated.
    for category in sorted(p.name for p in data_dir().iterdir() if p.is_dir()):
        if category not in DATA_SCHEMA_MAP:
            errors.append(
                f"project/Assets/Data/{category}: no governing schema is mapped "
                "for this category; add it to DATA_SCHEMA_MAP in scripts/_repo.py"
            )

    ids_by_category: dict[str, set[str]] = {}

    for category, schema_name in DATA_SCHEMA_MAP.items():
        directory = data_dir() / category
        if not (schema_dir() / schema_name).is_file():
            errors.append(f"project/Assets/Schema/{schema_name}: missing")
        if not directory.is_dir():
            warnings.append(
                f"project/Assets/Data/{category}: no data authored yet for this category"
            )
            ids_by_category[category] = set()
            continue

        ids: set[str] = set()
        for path in sorted(directory.glob("*.json")):
            documents += 1
            rel = path.relative_to(ROOT)
            try:
                document = load_json(path)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
                continue

            asset_id = document.get("id")
            if not asset_id:
                errors.append(f"{rel}: no 'id' field")
                continue
            if not ID_PATTERN.match(asset_id):
                errors.append(
                    f"{rel}: id '{asset_id}' is not lower_snake_case"
                )
            if asset_id != path.stem:
                errors.append(
                    f"{rel}: id '{asset_id}' does not match filename '{path.stem}'"
                )
            if asset_id in ids:
                errors.append(f"{rel}: duplicate id '{asset_id}' within {category}")
            ids.add(asset_id)
        ids_by_category[category] = ids

    # Orphans: an objective no mission references is content nothing can reach.
    referenced: set[str] = set()
    missions = data_dir() / "Missions"
    if missions.is_dir():
        for path in sorted(missions.glob("*.json")):
            try:
                document = load_json(path)
            except json.JSONDecodeError:
                continue
            referenced.update(document.get("objectives", []))

    for orphan in sorted(ids_by_category.get("Objectives", set()) - referenced):
        warnings.append(
            f"objective '{orphan}' is referenced by no mission; it is unreachable content"
        )

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print(f"Asset validation FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"Asset validation passed ({documents} documents across "
        f"{len(DATA_SCHEMA_MAP)} categories, {len(warnings)} warnings)."
    )


if __name__ == "__main__":
    main()
