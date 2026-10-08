"""Remove generated build, packaging and bytecode-cache directories."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    removed = []

    for name in ("build", "packages"):
        path = ROOT / name
        if path.exists():
            shutil.rmtree(path)
            removed.append(name)

    for cache in sorted(ROOT.rglob("__pycache__")):
        if ".git" in cache.parts:
            continue
        shutil.rmtree(cache, ignore_errors=True)
        removed.append(cache.relative_to(ROOT).as_posix())

    print(f"Clean complete ({len(removed)} paths removed).")


if __name__ == "__main__":
    main()
