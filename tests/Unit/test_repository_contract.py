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

    def test_gem_root_descends_into_code(self):
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                text = (gem / "CMakeLists.txt").read_text(encoding="utf-8")
                self.assertIn("add_subdirectory(Code)", text)

    def test_gem_root_calls_o3de_gem_setup(self):
        """o3de_gem_setup establishes the variables o3de_pal_dir needs."""
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                text = (gem / "CMakeLists.txt").read_text(encoding="utf-8")
                self.assertIn(f'o3de_gem_setup("{gem.name}")', text)

    def test_every_gem_declares_the_three_build_targets(self):
        """API interface, private object library and module, per docs/tdd/02.

        This shape is taken from the engine's own gems, not invented: an
        earlier two-target version would not have configured.
        """
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                text = (gem / "Code" / "CMakeLists.txt").read_text(encoding="utf-8")
                self.assertIn("NAME ${gem_name}.API INTERFACE", text)
                self.assertIn("NAME ${gem_name}.Private.Object STATIC", text)
                self.assertIn("NAME ${gem_name} ${PAL_TRAIT_MONOLITHIC_DRIVEN_MODULE_TYPE}", text)
                self.assertIn("O3DE_PRIVATE_TARGET TRUE", text)
                for role in ("Clients", "Servers", "Unified"):
                    self.assertIn(f"NAME ${{gem_name}}.{role} ", text)
                    self.assertIn(f"NAME ${{gem_name}}.{role}.API ", text)

    def test_every_gem_resolves_its_platform_dir(self):
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                text = (gem / "Code" / "CMakeLists.txt").read_text(encoding="utf-8")
                self.assertIn("o3de_pal_dir(pal_dir", text)
                self.assertIn("PAL_${PAL_PLATFORM_NAME_LOWERCASE}.cmake", text)

    def test_every_gem_has_the_three_file_lists(self):
        """Manual sources split api/private/shared; see chapter 90 C5."""
        for gem in gem_dirs():
            lower = gem.name.lower()
            for kind in ("api", "private", "shared"):
                with self.subTest(gem=gem.name, kind=kind):
                    self.assertTrue(
                        (gem / "Code" / f"{lower}_{kind}_files.cmake").is_file()
                    )

    def test_every_gem_has_platform_traits_and_file_lists(self):
        """PAL_<platform>.cmake for traits plus a list per file kind."""
        lower = str.lower
        for gem in gem_dirs():
            for platform in ("Windows", "Linux"):
                pal = gem / "Code" / "Platform" / platform
                with self.subTest(gem=gem.name, platform=platform):
                    self.assertTrue((pal / f"PAL_{lower(platform)}.cmake").is_file())
                    for kind in ("api", "private", "shared"):
                        self.assertTrue(
                            (pal / f"{lower(gem.name)}_{kind}_files.cmake").is_file(),
                            f"missing {platform} {kind} list for {gem.name}",
                        )

    def test_project_has_entry_point_and_target_lists(self):
        self.assertTrue((ROOT / "project" / "CMakeLists.txt").is_file())
        code = ROOT / "project" / "Code"
        self.assertTrue((code / "CMakeLists.txt").is_file())
        for kind in ("api", "private", "shared"):
            self.assertTrue((code / f"phoenix_{kind}_files.cmake").is_file())

    def test_the_three_responsibilities_stay_separate(self):
        """Manual sources, generated inputs and gem activation, per chapter 90 C5."""
        code = ROOT / "project" / "Code"
        autogen = (code / "Phoenix_autogen_files.cmake").read_text(encoding="utf-8")
        enabled = (code / "enabled_gems.cmake").read_text(encoding="utf-8")

        # Compare declared entries, not the prose: the comment legitimately
        # mentions the generated .cpp it tells you never to commit.
        entries = [
            line.strip()
            for line in autogen.splitlines()
            if line.startswith("    ") and not line.strip().startswith("#")
        ]
        self.assertTrue(entries)
        for entry in entries:
            self.assertTrue(
                entry.endswith(".AutoComponent.xml"),
                f"autogen list carries a non-XML entry: {entry}",
            )
        # Gem activation stays O3DE-managed and declares no files.
        self.assertNotIn("set(FILES", enabled)

    def test_build_presets_exist(self):
        presets = load_json(ROOT / "CMakePresets.json")
        names = {p["name"] for p in presets["configurePresets"]}
        self.assertIn("windows-client", names)
        self.assertIn("linux-server", names)
        build_names = {p["name"] for p in presets["buildPresets"]}
        self.assertTrue(any("profile" in n for n in build_names))

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
