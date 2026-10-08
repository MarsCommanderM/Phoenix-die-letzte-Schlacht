import json
import unittest

import sys
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import DATA_SCHEMA_MAP, data_dir, load_json, schema_dir

try:
    import jsonschema
except ImportError:  # pragma: no cover - exercised only without the dev extra
    jsonschema = None


class SchemaFileTests(unittest.TestCase):
    def test_all_schema_files_are_valid_json(self):
        files = list(schema_dir().glob("*.schema.json"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(path=path.name):
                json.loads(path.read_text(encoding="utf-8"))

    @unittest.skipIf(jsonschema is None, "jsonschema not installed")
    def test_all_schema_files_are_valid_schemas(self):
        for path in schema_dir().glob("*.schema.json"):
            with self.subTest(path=path.name):
                jsonschema.Draft202012Validator.check_schema(load_json(path))

    @unittest.skipIf(jsonschema is None, "jsonschema not installed")
    def test_sample_data_conforms_to_its_schema(self):
        for category, schema_name in DATA_SCHEMA_MAP.items():
            schema = load_json(schema_dir() / schema_name)
            directory = data_dir() / category
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json")):
                with self.subTest(document=f"{category}/{path.name}"):
                    jsonschema.Draft202012Validator(schema).validate(load_json(path))

    def test_data_ids_match_filenames(self):
        for category in DATA_SCHEMA_MAP:
            directory = data_dir() / category
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json")):
                with self.subTest(document=f"{category}/{path.name}"):
                    self.assertEqual(load_json(path)["id"], path.stem)


if __name__ == "__main__":
    unittest.main()
