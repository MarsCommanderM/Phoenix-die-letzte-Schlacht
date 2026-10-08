import unittest

import sys
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT, gem_dirs, load_json

EXPECTED_GEMS = {
    "PhoenixCore",
    "PhoenixGameplay",
    "PhoenixCharacter",
    "PhoenixAI",
    "PhoenixWorld",
    "PhoenixPresentation",
    "PhoenixNetworking",
    "PhoenixTools",
}


class RepositoryContractTests(unittest.TestCase):
    def test_project_manifest(self):
        data = load_json(ROOT / "project" / "project.json")
        self.assertEqual(data["project_name"], "Phoenix")
        self.assertIn("canonical_tags", data)
        self.assertIn("external_subdirectories", data)
        self.assertEqual(data["canonical_tags"], ["Project"])

    def test_gem_set_matches_expectation(self):
        # Identify gems by manifest rather than counting entries in gems/, so
        # an unrelated file in that directory does not fail the contract.
        self.assertEqual({gem.name for gem in gem_dirs()}, EXPECTED_GEMS)

    def test_gem_manifests(self):
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                data = load_json(gem / "gem.json")
                self.assertEqual(data["gem_name"], gem.name)
                self.assertEqual(data["canonical_tags"], ["Gem"])
                self.assertEqual(data["type"], "Code")

    def test_project_external_subdirectories_match_disk(self):
        data = load_json(ROOT / "project" / "project.json")
        declared = {entry.split("/")[-1] for entry in data["external_subdirectories"]}
        self.assertEqual(declared, {gem.name for gem in gem_dirs()})

    def test_every_gem_declares_its_name_in_cmake(self):
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                text = (gem / "CMakeLists.txt").read_text(encoding="utf-8")
                self.assertIn(f"set(PHOENIX_GEM_NAME {gem.name})", text)

    def test_machine_local_user_directory_is_not_committed(self):
        # .gitignore excludes user/; shipping project/user/ would be both
        # ignored and misleading.
        self.assertFalse((ROOT / "project" / "user").exists())

    def test_workflows_live_where_github_runs_them(self):
        workflows = sorted(p.name for p in (ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertEqual(
            workflows, ["nightly.yml", "pull_request.yml", "release.yml", "server.yml"]
        )
        self.assertFalse((ROOT / "ci").exists(), "ci/ workflows would never run")


if __name__ == "__main__":
    unittest.main()
