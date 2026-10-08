"""Validate the Phoenix project and gem manifest contract.

Complements scripts/validate.py: that script is the CI gate over the whole
repository, this one answers "is the project itself well formed" and is the
tool to reach for when O3DE refuses to register the project.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from _repo import gem_dirs, load_json  # noqa: E402

REQUIRED_PROJECT_FIELDS = (
    "project_name",
    "project_id",
    "origin",
    "canonical_tags",
    "compatible_engines",
    "external_subdirectories",
)
REQUIRED_GEM_FIELDS = (
    "gem_name",
    "display_name",
    "version",
    "license",
    "origin",
    "type",
    "summary",
    "canonical_tags",
    "compatible_engines",
)

#: Engine gems verified to exist at O3DE tag 2605.0.
#: See docs/adr/0010-engine-dependency-verification.md.
KNOWN_ENGINE_GEMS = frozenset(
    {
        "Atom",
        "EMotionFX",
        "Multiplayer",
        "AudioSystem",
        "LyShine",
        "PhysX5",
        "RecastNavigation",
        "LmbrCentral",
        "PrefabBuilder",
        "SaveData",
    }
)
#: Names that look like gems but are not, at that tag. Declaring one of these
#: fails at `o3de enable-gem`, or worse succeeds and means something else.
KNOWN_BAD_GEMS = {
    "PhysX": "PhysX is the PhysX 4 gem; this project pins PhysX 5, whose gem is 'PhysX5'",
    "Navigation": "no gem named 'Navigation' exists; use 'RecastNavigation'",
    "Prefab": "not a gem; runtime prefab support is in AzFramework",
}


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    project = load_json(ROOT / "project" / "project.json")
    for field in REQUIRED_PROJECT_FIELDS:
        if field not in project:
            errors.append(f"project.json: missing required field '{field}'")

    engines = project.get("compatible_engines", [])
    if not any(e.startswith("o3de==") for e in engines):
        errors.append(
            "project.json: compatible_engines should pin an exact engine "
            f"(o3de==<version>), found {engines}"
        )

    declared = {e.split("/")[-1] for e in project.get("external_subdirectories", [])}
    on_disk = {g.name for g in gem_dirs()}
    for only_manifest in sorted(declared - on_disk):
        errors.append(
            f"project.json: external_subdirectories names '{only_manifest}', "
            "which is not a gem directory"
        )
    for only_disk in sorted(on_disk - declared):
        errors.append(
            f"gems/{only_disk}: present on disk but not in "
            "project.json external_subdirectories, so O3DE will not see it"
        )

    phoenix_gems = on_disk
    for gem in gem_dirs():
        manifest = load_json(gem / "gem.json")
        for field in REQUIRED_GEM_FIELDS:
            if field not in manifest:
                errors.append(f"gems/{gem.name}/gem.json: missing field '{field}'")
        if manifest.get("gem_name") != gem.name:
            errors.append(
                f"gems/{gem.name}/gem.json: gem_name "
                f"'{manifest.get('gem_name')}' does not match the directory"
            )
        for dep in manifest.get("dependencies", []):
            if dep in KNOWN_BAD_GEMS:
                errors.append(f"gems/{gem.name}/gem.json: {KNOWN_BAD_GEMS[dep]}")
            elif dep not in phoenix_gems and dep not in KNOWN_ENGINE_GEMS:
                warnings.append(
                    f"gems/{gem.name}/gem.json: dependency '{dep}' is neither a "
                    "Phoenix gem nor a known engine gem; verify it against the "
                    "registered engine"
                )

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print(f"Project validation FAILED ({len(errors)} problems):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"Project validation passed ({len(on_disk)} gems, "
        f"{len(warnings)} warnings)."
    )


if __name__ == "__main__":
    main()
