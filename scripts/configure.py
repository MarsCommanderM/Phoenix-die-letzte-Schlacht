"""Report where the Phoenix project lives, for O3DE registration."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "project"


def main() -> None:
    print(f"Phoenix project: {PROJECT}")
    print("Use the O3DE 26.05.0 CLI/Project Manager to register and configure this project.")
    print("This script intentionally does not guess a local O3DE installation path.")


if __name__ == "__main__":
    main()
