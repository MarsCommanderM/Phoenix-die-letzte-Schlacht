from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packages"
OUT.mkdir(exist_ok=True)
archive = OUT / "Phoenix-source-package.zip"

with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in ROOT.rglob("*"):
        if p.is_file() and "packages" not in p.parts and "build" not in p.parts:
            zf.write(p, p.relative_to(ROOT))

print(archive)
