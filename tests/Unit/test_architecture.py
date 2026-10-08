import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import check_architecture
from _repo import ROOT

GEM_MANIFEST = {
    "gem_name": "",
    "version": "0.1.0",
    "type": "Code",
    "canonical_tags": ["Gem"],
    "dependencies": [],
}


def make_gem(root: Path, name: str, dependencies=()) -> Path:
    """A gem skeleton: the manifest plus the public/private header split.

    Every rule is exercised against a constructed tree as well as against the
    committed one, because a gate that has only ever been run on a tree that
    already satisfies it has never been seen to fail. Each root is resolved,
    as _repo.ROOT is, so include targets resolved through a symlinked
    temporary directory still compare equal.
    """
    gem = root / "gems" / name
    (gem / "Code" / "Include" / "Phoenix" / name).mkdir(parents=True, exist_ok=True)
    (gem / "Code" / "Source").mkdir(parents=True, exist_ok=True)
    manifest = dict(GEM_MANIFEST, gem_name=name, dependencies=list(dependencies))
    (gem / "gem.json").write_text(json.dumps(manifest), encoding="utf-8")
    return gem


def make_project(root: Path) -> Path:
    """The minimum project tree the AutoComponent rule reads."""
    code = root / "project" / "Code"
    (code / "Source" / "AutoGen").mkdir(parents=True, exist_ok=True)
    return code


def write_autogen_cmake(code: Path, entries) -> None:
    body = "\n".join(f"    {entry}" for entry in entries)
    (code / "Phoenix_autogen_files.cmake").write_text(
        f"set(PHOENIX_AUTOGEN_FILES\n{body}\n)\n", encoding="utf-8"
    )


class GateHoldsOnTheCommittedTreeTests(unittest.TestCase):
    """The committed tree must satisfy the gate CI runs."""

    def test_check_architecture_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_architecture.py")],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_summary_reports_counts(self):
        """A gate that cannot say what it covered cannot be trusted."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_architecture.py")],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertIn("gems", result.stdout)
        self.assertIn("includes in", result.stdout)
        self.assertIn("AutoComponent XMLs", result.stdout)
        self.assertIn("top-level areas owned", result.stdout)

    def test_docstring_names_the_unimplemented_rules(self):
        """Section 273 lists eight rules; four are out of reach today.

        The docstring is where that is recorded, so a later reader does not
        mistake four passing checks for all eight.
        """
        docstring = check_architecture.__doc__
        for missing in (
            "No missing tests for required systems",
            "No invalid asset references",
            "No broken schemas",
            "No unexpected engine changes",
        ):
            with self.subTest(rule=missing):
                self.assertIn(missing, docstring)


class CycleDetectionTests(unittest.TestCase):
    def test_acyclic_graph_has_no_cycles(self):
        graph = {"A": ["B", "C"], "B": ["C"], "C": []}
        self.assertEqual(check_architecture.find_cycles(graph), [])

    def test_direct_cycle(self):
        graph = {"A": ["B"], "B": ["A"]}
        self.assertEqual(check_architecture.find_cycles(graph), [["A", "B"]])

    def test_indirect_cycle_reports_the_whole_path(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(check_architecture.find_cycles(graph), [["A", "B", "C"]])

    def test_self_dependency_is_a_cycle(self):
        self.assertEqual(check_architecture.find_cycles({"A": ["A"]}), [["A"]])

    def test_a_cycle_is_reported_once_not_once_per_member(self):
        graph = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(len(check_architecture.find_cycles(graph)), 1)

    def test_cycle_in_gem_manifests_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            make_gem(root, "PhoenixCore", ["PhoenixPresentation"])
            make_gem(root, "PhoenixGameplay", ["PhoenixCore"])
            make_gem(root, "PhoenixPresentation", ["PhoenixGameplay"])
            errors: list[str] = []
            check_architecture.check_gem_cycles(root, errors)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn(
                "PhoenixCore -> PhoenixPresentation -> PhoenixGameplay -> PhoenixCore",
                errors[0],
            )

    def test_engine_dependencies_cannot_close_a_cycle(self):
        """Engine gems are O3DE's to order and must not enter the graph."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            make_gem(root, "PhoenixCore", ["Multiplayer", "Atom"])
            graph = check_architecture.gem_dependency_graph(root)
            self.assertEqual(graph, {"PhoenixCore": []})


class ForbiddenIncludeTests(unittest.TestCase):
    def _scan(self, root: Path) -> list[str]:
        errors: list[str] = []
        check_architecture.check_forbidden_includes(root, errors)
        return errors

    def test_public_cross_gem_include_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            core = make_gem(root, "PhoenixCore")
            (core / "Code" / "Include" / "Phoenix" / "Core").mkdir(parents=True)
            (
                core / "Code" / "Include" / "Phoenix" / "Core" / "PhoenixIds.h"
            ).write_text("#pragma once\n", encoding="utf-8")
            gameplay = make_gem(root, "PhoenixGameplay", ["PhoenixCore"])
            (gameplay / "Code" / "Source" / "Rules.cpp").write_text(
                "#include <Phoenix/Core/PhoenixIds.h>\n", encoding="utf-8"
            )
            self.assertEqual(self._scan(root), [])

    def test_including_another_gems_source_header_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            gameplay = make_gem(root, "PhoenixGameplay")
            (gameplay / "Code" / "Source" / "GameplayInternals.h").write_text(
                "#pragma once\n", encoding="utf-8"
            )
            presentation = make_gem(root, "PhoenixPresentation", ["PhoenixGameplay"])
            (presentation / "Code" / "Source" / "Hud.cpp").write_text(
                "#include <GameplayInternals.h>\n", encoding="utf-8"
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("Hud.cpp:1", errors[0])
            self.assertIn("GameplayInternals.h", errors[0])
            self.assertIn("private Source/ tree", errors[0])

    def test_spelling_a_route_into_another_source_tree_fails(self):
        """The route is the violation, whether or not the header exists yet."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            make_gem(root, "PhoenixGameplay")
            presentation = make_gem(root, "PhoenixPresentation")
            (presentation / "Code" / "Source" / "Hud.cpp").write_text(
                "#include <PhoenixGameplay/Code/Source/NotYetWritten.h>\n",
                encoding="utf-8",
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("names a route into another", errors[0])

    def test_relative_escape_into_another_source_tree_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            core = make_gem(root, "PhoenixCore")
            (core / "Code" / "Source" / "CoreInternals.h").write_text(
                "#pragma once\n", encoding="utf-8"
            )
            tools = make_gem(root, "PhoenixTools", ["PhoenixCore"])
            (tools / "Code" / "Source" / "Inspector.cpp").write_text(
                '#include "../../../PhoenixCore/Code/Source/CoreInternals.h"\n',
                encoding="utf-8",
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("names a route into another", errors[0])

    def test_own_private_header_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            core = make_gem(root, "PhoenixCore")
            (core / "Code" / "Source" / "CoreInternals.h").write_text(
                "#pragma once\n", encoding="utf-8"
            )
            (core / "Code" / "Source" / "Core.cpp").write_text(
                '#include "CoreInternals.h"\n#include <CoreInternals.h>\n',
                encoding="utf-8",
            )
            self.assertEqual(self._scan(root), [])

    def test_rendering_headers_outside_presentation_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            gameplay = make_gem(root, "PhoenixGameplay")
            (gameplay / "Code" / "Source" / "Rules.cpp").write_text(
                "#include <Atom/RPI.Public/Pass/Pass.h>\n"
                "#include <LyShine/Bus/UiCanvasBus.h>\n"
                "#include <AzFramework/Render/GeometryIntersectionBus.h>\n",
                encoding="utf-8",
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 3, errors)
            for error in errors:
                self.assertIn("rendering header", error)

    def test_rendering_headers_inside_presentation_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            presentation = make_gem(root, "PhoenixPresentation")
            (presentation / "Code" / "Source" / "Renderer.cpp").write_text(
                "#include <Atom/RPI.Public/Pass/Pass.h>\n"
                "#include <LyShine/Bus/UiCanvasBus.h>\n",
                encoding="utf-8",
            )
            self.assertEqual(self._scan(root), [])

    def test_multiplayer_headers_outside_networking_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            world = make_gem(root, "PhoenixWorld")
            (world / "Code" / "Source" / "Cell.cpp").write_text(
                "#include <Multiplayer/IMultiplayer.h>\n", encoding="utf-8"
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("Multiplayer header", errors[0])

    def test_multiplayer_headers_inside_networking_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            networking = make_gem(root, "PhoenixNetworking")
            (networking / "Code" / "Source" / "Replication.cpp").write_text(
                "#include <Multiplayer/IMultiplayer.h>\n", encoding="utf-8"
            )
            self.assertEqual(self._scan(root), [])

    def test_engine_includes_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            core = make_gem(root, "PhoenixCore")
            (core / "Code" / "Source" / "Core.cpp").write_text(
                "#include <AzCore/Component/Component.h>\n"
                "#include <AzFramework/Entity/GameEntityContextBus.h>\n",
                encoding="utf-8",
            )
            self.assertEqual(self._scan(root), [])

    def test_project_may_not_reach_into_a_gems_source_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            core = make_gem(root, "PhoenixCore")
            (core / "Code" / "Source" / "CoreInternals.h").write_text(
                "#pragma once\n", encoding="utf-8"
            )
            code = make_project(root)
            (code / "Source" / "PhoenixModule.cpp").write_text(
                "#include <CoreInternals.h>\n", encoding="utf-8"
            )
            errors = self._scan(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("private Source/ tree", errors[0])


class AutoComponentRegistrationTests(unittest.TestCase):
    def _check(self, root: Path) -> list[str]:
        errors: list[str] = []
        check_architecture.check_autogen_registration(root, errors)
        return errors

    def test_declared_and_present_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            code = make_project(root)
            (code / "Source" / "AutoGen" / "A.AutoComponent.xml").write_text(
                "<Component/>", encoding="utf-8"
            )
            write_autogen_cmake(code, ["Source/AutoGen/A.AutoComponent.xml"])
            self.assertEqual(self._check(root), [])

    def test_unlisted_xml_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            code = make_project(root)
            (code / "Source" / "AutoGen" / "A.AutoComponent.xml").write_text(
                "<Component/>", encoding="utf-8"
            )
            (code / "Source" / "AutoGen" / "B.AutoComponent.xml").write_text(
                "<Component/>", encoding="utf-8"
            )
            write_autogen_cmake(code, ["Source/AutoGen/A.AutoComponent.xml"])
            errors = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("B.AutoComponent.xml", errors[0])
            self.assertIn("silently never exists", errors[0])

    def test_declared_but_missing_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            code = make_project(root)
            write_autogen_cmake(code, ["Source/AutoGen/Gone.AutoComponent.xml"])
            errors = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("declares missing path", errors[0])

    def test_missing_cmake_list_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            make_project(root)
            errors = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("missing", errors[0])

    def test_comments_in_the_list_are_not_treated_as_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            code = make_project(root)
            (code / "Source" / "AutoGen" / "A.AutoComponent.xml").write_text(
                "<Component/>", encoding="utf-8"
            )
            (code / "Phoenix_autogen_files.cmake").write_text(
                "set(PHOENIX_AUTOGEN_FILES\n"
                "    # the player component\n"
                "    Source/AutoGen/A.AutoComponent.xml\n"
                ")\n",
                encoding="utf-8",
            )
            self.assertEqual(self._check(root), [])


class CodeownersTests(unittest.TestCase):
    def _check(self, root: Path):
        errors: list[str] = []
        warnings: list[str] = []
        check_architecture.check_codeowners(root, errors, warnings)
        return errors, warnings

    def _areas(self, root: Path) -> None:
        for area in check_architecture.OWNED_AREAS:
            (root / area).mkdir(parents=True, exist_ok=True)

    def test_pattern_matching(self):
        for pattern, area, expected in (
            ("*", "gems", True),
            ("/gems/", "gems", True),
            ("gems", "gems", True),
            ("gems/*", "gems", True),
            ("gems/**", "gems", True),
            (".github/", ".github", True),
            ("gems/PhoenixCore/", "gems", False),
            ("docs/", "gems", False),
        ):
            with self.subTest(pattern=pattern, area=area):
                self.assertEqual(
                    check_architecture.covers_area(pattern, area), expected
                )

    def test_named_owners_per_area_pass_without_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            lines = [
                f"/{area}/ @owner-{area.strip('.')}"
                for area in check_architecture.OWNED_AREAS
            ]
            (root / "CODEOWNERS").write_text(
                "\n".join(lines) + "\n", encoding="utf-8"
            )
            errors, warnings = self._check(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_catch_all_only_warns_rather_than_passing_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            (root / "CODEOWNERS").write_text("* @owner\n", encoding="utf-8")
            errors, warnings = self._check(root)
            self.assertEqual(errors, [])
            self.assertEqual(len(warnings), 1, warnings)
            self.assertIn("catch-all", warnings[0])
            self.assertIn("weak pass", warnings[0])

    def test_uncovered_area_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            (root / "CODEOWNERS").write_text("/gems/ @owner\n", encoding="utf-8")
            errors, _ = self._check(root)
            self.assertEqual(len(errors), len(check_architecture.OWNED_AREAS) - 1)
            self.assertTrue(all("no pattern covers" in e for e in errors))

    def test_pattern_without_an_owner_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            (root / "CODEOWNERS").write_text("*\n", encoding="utf-8")
            errors, _ = self._check(root)
            self.assertTrue(any("has no owner" in e for e in errors), errors)

    def test_missing_codeowners_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            errors, _ = self._check(root)
            self.assertEqual(len(errors), 1, errors)
            self.assertIn("no CODEOWNERS file", errors[0])

    def test_github_location_is_honoured(self):
        """GitHub reads .github/CODEOWNERS too; so must this rule."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self._areas(root)
            (root / ".github" / "CODEOWNERS").write_text(
                "* @owner\n", encoding="utf-8"
            )
            errors, warnings = self._check(root)
            self.assertEqual(errors, [])
            self.assertIn(".github/CODEOWNERS", warnings[0])


if __name__ == "__main__":
    unittest.main()
