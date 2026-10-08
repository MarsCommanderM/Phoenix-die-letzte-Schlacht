import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

class RepositoryContractTests(unittest.TestCase):
    def test_project_manifest(self):
        data = json.loads((ROOT / "project/project.json").read_text(encoding="utf-8"))
        self.assertEqual(data["project_name"], "Phoenix")
        self.assertIn("canonical_tags", data)
        self.assertIn("external_subdirectories", data)

    def test_gems_have_manifests(self):
        gems = list((ROOT / "gems").iterdir())
        self.assertEqual(len(gems), 8)
        for gem in gems:
            data = json.loads((gem / "gem.json").read_text(encoding="utf-8"))
            self.assertEqual(data["canonical_tags"], ["Gem"])
            self.assertEqual(data["type"], "Code")

if __name__ == "__main__":
    unittest.main()
