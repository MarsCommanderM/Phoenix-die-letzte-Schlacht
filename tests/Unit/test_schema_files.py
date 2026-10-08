import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class SchemaFileTests(unittest.TestCase):
    def test_all_schema_files_are_valid_json(self):
        schema_dir = ROOT / "project" / "Assets" / "Schema"
        files = list(schema_dir.glob("*.schema.json"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
