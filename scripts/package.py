"""Package the Phoenix source tree for distribution.

The imported starter excluded only build/ and packages/, which meant the
entire .git directory -- full history and any credentials ever committed --
was written into the release archive. Exclusions now come from
_repo.EXCLUDED_TOP_LEVEL and are anchored at the repository root.
"""
from __future__ import annotations

import zipfile

import sys
from pathlib import Path

# Make the sibling _repo helper importable regardless of cwd or isolated mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import ROOT, iter_source_files

OUT = ROOT / "packages"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    archive = OUT / "Phoenix-source-package.zip"

    count = 0
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in iter_source_files():
            zf.write(path, path.relative_to(ROOT))
            count += 1

    print(f"{archive} ({count} files)")


if __name__ == "__main__":
    main()
