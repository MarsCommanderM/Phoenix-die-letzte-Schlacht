"""Migrate a Phoenix save from any supported older schema version to current.

docs/tdd/06-data-schemas.md requires migrations to be deterministic and
tested, and acceptance criterion 5 requires save schemas to be migratable.
This is the runner those requirements refer to.

Design notes:

- Migrations form a chain, applied in order. There is no "migrate from v1
  straight to v4" shortcut, because every such shortcut is a second code path
  that drifts from the chain it duplicates.
- Each migration is a pure function: it takes a document and returns a new
  one. No I/O, no clock, no randomness, so a migration is reproducible and
  testable.
- A save newer than this build is rejected rather than guessed at.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]

#: The schema version this build writes.
CURRENT_SCHEMA_VERSION = 2

Migration = Callable[[dict], dict]


def _v1_to_v2(document: dict) -> dict:
    """v1 -> v2: a campaign holds a list of missions, and player state is split out.

    v1 stored a single `campaign.mission` and kept player progress inside the
    campaign block. v2 separates persistent player state from campaign state,
    because they have different lifetimes: a player keeps progression across
    campaigns.
    """
    out = copy.deepcopy(document)
    campaign = out.setdefault("campaign", {})

    mission = campaign.pop("mission", None)
    campaign["missions"] = [mission] if mission is not None else []

    player = {}
    for key in ("progression", "unlocks"):
        if key in campaign:
            player[key] = campaign.pop(key)
    out["player"] = player

    out["schemaVersion"] = 2
    return out


#: Keyed by the version being migrated FROM.
MIGRATIONS: dict[int, Migration] = {
    1: _v1_to_v2,
}


def migrate(document: dict) -> tuple[dict, list[str]]:
    """Return the migrated document and the chain of steps applied."""
    if "schemaVersion" not in document:
        raise ValueError("save has no schemaVersion; cannot determine its format")

    version = document["schemaVersion"]
    if not isinstance(version, int):
        raise ValueError(f"schemaVersion must be an integer, got {version!r}")
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            f"save is version {version}, newer than this build's "
            f"{CURRENT_SCHEMA_VERSION}; refusing to guess at a downgrade"
        )

    applied: list[str] = []
    while version < CURRENT_SCHEMA_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(
                f"no migration registered from version {version}; the chain to "
                f"{CURRENT_SCHEMA_VERSION} is broken"
            )
        document = migration(document)
        applied.append(f"v{version} -> v{version + 1}")
        new_version = document.get("schemaVersion")
        if new_version != version + 1:
            raise ValueError(
                f"migration from v{version} left schemaVersion at {new_version}; "
                "a migration must advance exactly one version"
            )
        version = new_version

    return document, applied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path, help="save file to migrate")
    parser.add_argument(
        "--out", type=Path, help="write here instead of stdout; '-' forces stdout"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would happen without writing anything",
    )
    args = parser.parse_args()

    document = json.loads(args.save.read_text(encoding="utf-8"))
    original = document.get("schemaVersion")

    try:
        migrated, applied = migrate(document)
    except ValueError as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not applied:
        print(f"{args.save}: already at version {CURRENT_SCHEMA_VERSION}; nothing to do.")
        return

    print(f"{args.save}: v{original} -> v{migrated['schemaVersion']} ({', '.join(applied)})")

    if args.check:
        return

    text = json.dumps(migrated, indent=4) + "\n"
    if args.out and str(args.out) != "-":
        args.out.write_text(text, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
