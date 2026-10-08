from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parents[1]
files = []
for p in ROOT.rglob("*"):
    if p.is_file() and ".git" not in p.parts and "build" not in p.parts and "packages" not in p.parts:
        data = p.read_bytes()
        files.append({
            "path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data)
        })

out = ROOT / "build" / "source_manifest.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"project":"Phoenix","files":files}, indent=2), encoding="utf-8")
print(out)
