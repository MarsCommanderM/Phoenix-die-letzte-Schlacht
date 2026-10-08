from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
for name in ("build", "packages"):
    p = ROOT / name
    if p.exists():
        shutil.rmtree(p)
print("Clean complete.")
