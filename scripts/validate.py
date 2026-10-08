from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def main():
    errors = []
    for path in (ROOT / "project" / "Assets" / "Schema").glob("*.schema.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print("Phoenix static validation passed.")

if __name__ == "__main__":
    main()
