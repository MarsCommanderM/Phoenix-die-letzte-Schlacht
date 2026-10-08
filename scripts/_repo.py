"""Shared repository-layout helpers for the Phoenix scripts and tests."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: Top-level directories that never belong in a manifest or source package.
EXCLUDED_TOP_LEVEL = frozenset({".git", ".github", "build", "packages", "__pycache__"})

#: Maps an asset data directory to the schema that governs it.
DATA_SCHEMA_MAP = {
    "Actions": "action.schema.json",
    "Missions": "mission.schema.json",
    "Objectives": "objective.schema.json",
}


def schema_dir() -> Path:
    return ROOT / "project" / "Assets" / "Schema"


def data_dir() -> Path:
    return ROOT / "project" / "Assets" / "Data"


def gem_dirs() -> list[Path]:
    """Gem directories, identified by the presence of a gem.json manifest.

    Detecting gems by manifest rather than by counting entries in gems/ keeps
    the contract stable when an unrelated file lands in that directory.
    """
    gems = ROOT / "gems"
    return sorted(p for p in gems.iterdir() if (p / "gem.json").is_file())


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_excluded(path: Path) -> bool:
    """True when path lies under an excluded top-level directory.

    Anchored at the repository root on purpose: a nested directory that
    happens to be called build/ or packages/ is still project content.
    """
    rel = path.relative_to(ROOT)
    return rel.parts and rel.parts[0] in EXCLUDED_TOP_LEVEL


def iter_source_files():
    """Every committed-content file, excluding generated and VCS directories."""
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and not is_excluded(path):
            yield path
