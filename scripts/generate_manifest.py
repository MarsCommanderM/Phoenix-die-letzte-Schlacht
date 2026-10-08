"""Write a hash manifest of the Phoenix source tree."""
from __future__ import annotations

import hashlib
import json

import sys
from pathlib import Path

# Make the sibling _repo helper importable regardless of cwd or isolated mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import ROOT, iter_source_files


def main() -> None:
    files = []
    for path in iter_source_files():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": digest.hexdigest(),
                "size": path.stat().st_size,
            }
        )

    out = ROOT / "build" / "source_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"project": "Phoenix", "files": files}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{out} ({len(files)} files)")


if __name__ == "__main__":
    main()
