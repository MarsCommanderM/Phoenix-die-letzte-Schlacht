"""What can be tested about the bring-up script without an O3DE engine.

The script's job is done on a machine this repository has never seen, in a
session where a wrong command costs an hour. Most of it cannot be exercised
here -- there is no engine -- so this covers the parts that are pure, and the
module docstring says plainly that the rest is unexercised. The alternative,
testing nothing because the interesting half is unreachable, would leave the
version parsing, the verdict rules, the command shapes and the failure
diagnosis to be discovered wrong at exactly the wrong moment.

The one check here that reads the real repository is the gem-activation one,
and it currently asserts that *nothing* is enabled. That is true today and is
the single fact most likely to waste tomorrow: a cmake configure run before
enable-gem succeeds and silently produces a project with no Phoenix code.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import bringup  # noqa: E402
from _repo import gem_dirs  # noqa: E402


def healthy() -> bringup.Facts:
    """A machine with nothing wrong with it, as the baseline for the rules."""
    return bringup.Facts(
        system="Linux",
        release="6.8.0",
        machine="x86_64",
        cpu_count=32,
        ram_gb=64.0,
        free_gb=400.0,
        free_gb_path="/teamspace/studios/this_studio/Phoenix",
        python="3.11.9",
        cmake=(3, 28, 3),
        ninja=(1, 11, 1),
        clang=(18, 1, 8),
        gcc=(13, 2, 0),
        git=(2, 45, 0),
        has_display=True,
        has_vulkan=True,
        gpu=None,
        persistent_root="/teamspace/studios/this_studio",
        repo_persistent=True,
        engine="/teamspace/studios/this_studio/o3de",
        engine_cli="/teamspace/studios/this_studio/o3de/scripts/o3de.sh",
    )


def levels(facts, min_free=120, min_ram=16) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"blocker": [], "warning": [], "note": []}
    for verdict in bringup.classify(facts, min_free, min_ram):
        out[verdict.level].append(verdict.subject)
    return out


class VersionParsingTests(unittest.TestCase):
    def test_the_real_output_shapes(self):
        """Each of these is what the tool actually prints."""
        cases = {
            "cmake version 3.28.3": (3, 28, 3),
            "1.11.1": (1, 11, 1),
            "Ubuntu clang version 18.1.3 (1ubuntu1)": (18, 1, 3),
            "clang-format version 18.1.8": (18, 1, 8),
            "git version 2.55.0": (2, 55, 0),
            "gcc (Ubuntu 13.2.0-23ubuntu4) 13.2.0": (13, 2, 0),
            "ninja 1.11": (1, 11),
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(bringup.parse_version(text), expected)

    def test_no_version_is_none_not_a_crash(self):
        for text in ("", "command not found", None):
            with self.subTest(text=text):
                self.assertIsNone(bringup.parse_version(text))

    def test_versions_compare_as_tuples(self):
        """The cmake blocker relies on this ordering being right."""
        self.assertLess(bringup.parse_version("cmake version 3.21.0"), (3, 22))
        self.assertGreater(bringup.parse_version("cmake version 3.28.3"), (3, 22))


class VerdictTests(unittest.TestCase):
    def test_a_healthy_machine_has_no_blockers(self):
        """Guards every negative case below: a rule set that always blocks is useless."""
        self.assertEqual(levels(healthy())["blocker"], [])

    def test_a_missing_engine_blocks(self):
        facts = healthy()
        facts.engine_cli = None
        self.assertIn("engine", levels(facts)["blocker"])

    def test_a_missing_cmake_blocks(self):
        facts = healthy()
        facts.cmake = None
        self.assertIn("cmake", levels(facts)["blocker"])

    def test_an_old_cmake_blocks(self):
        facts = healthy()
        facts.cmake = (3, 21, 0)
        self.assertIn("cmake", levels(facts)["blocker"])

    def test_no_compiler_blocks(self):
        facts = healthy()
        facts.clang = None
        facts.gcc = None
        self.assertIn("compiler", levels(facts)["blocker"])

    def test_either_compiler_alone_is_enough(self):
        for drop in ("clang", "gcc"):
            with self.subTest(dropped=drop):
                facts = healthy()
                setattr(facts, drop, None)
                self.assertNotIn("compiler", levels(facts)["blocker"])

    def test_too_little_disk_blocks(self):
        facts = healthy()
        facts.free_gb = 30.0
        self.assertIn("disk", levels(facts)["blocker"])

    def test_the_disk_threshold_is_adjustable(self):
        """It is a planning figure, not a vendor spec, so it must be overridable."""
        facts = healthy()
        facts.free_gb = 30.0
        self.assertNotIn("disk", levels(facts, min_free=20)["blocker"])

    def test_low_ram_warns_rather_than_blocks(self):
        """A low-RAM build may still succeed with less parallelism."""
        facts = healthy()
        facts.ram_gb = 8.0
        result = levels(facts)
        self.assertIn("ram", result["warning"])
        self.assertNotIn("ram", result["blocker"])

    def test_no_persistent_root_warns(self):
        facts = healthy()
        facts.persistent_root = None
        facts.repo_persistent = None
        self.assertIn("persistence", levels(facts)["warning"])

    def test_a_repo_outside_the_persistent_root_warns(self):
        """The failure that costs a whole day: hours of build, then discarded."""
        facts = healthy()
        facts.repo_persistent = False
        self.assertIn("persistence", levels(facts)["warning"])

    def test_an_engine_outside_the_persistent_root_warns(self):
        facts = healthy()
        facts.engine = "/tmp/o3de"
        self.assertIn("persistence", levels(facts)["warning"])

    def test_an_attached_gpu_warns_because_compiling_does_not_use_it(self):
        facts = healthy()
        facts.gpu = "Tesla T4"
        warnings = [
            v for v in bringup.classify(facts, 120, 16) if v.subject == "gpu"
        ]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].level, "warning")
        self.assertIn("compiling uses none of it", warnings[0].detail)

    def test_a_headless_machine_is_a_note_not_a_blocker(self):
        """Headless is the normal case for a server build, not a fault."""
        facts = healthy()
        facts.has_display = False
        result = levels(facts)
        self.assertIn("display", result["note"])
        self.assertEqual(result["blocker"], [])

    def test_missing_ninja_is_called_out(self):
        facts = healthy()
        facts.ninja = None
        self.assertIn("ninja", levels(facts)["note"])


class PresetTests(unittest.TestCase):
    def test_linux_maps_to_the_server_preset(self):
        """It is also the only Linux preset CMakePresets.json defines."""
        facts = healthy()
        self.assertEqual(bringup.preset_for(facts), "linux-server")

    def test_windows_maps_to_the_client_preset(self):
        facts = healthy()
        facts.system = "Windows"
        self.assertEqual(bringup.preset_for(facts), "windows-client")

    def test_an_unsupported_platform_returns_none_rather_than_guessing(self):
        facts = healthy()
        facts.system = "Darwin"
        self.assertIsNone(bringup.preset_for(facts))

    def test_the_presets_named_here_exist_in_cmakepresets(self):
        """Otherwise the script would hand cmake a preset it does not have."""
        import json

        document = json.loads((ROOT / "CMakePresets.json").read_text(encoding="utf-8"))
        names = {p["name"] for p in document["configurePresets"]}
        for system in ("Linux", "Windows"):
            facts = healthy()
            facts.system = system
            with self.subTest(system=system):
                self.assertIn(bringup.preset_for(facts), names)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.steps = bringup.plan(healthy(), "linux-server")
        self.names = [step.name for step in self.steps]

    def test_every_phoenix_gem_is_enabled(self):
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                self.assertIn(f"enable {gem.name}", self.names)

    def test_the_order_is_register_then_enable_then_configure(self):
        """Each depends on the one before; a wrong order fails for a wrong reason."""
        register = self.names.index("register project")
        first_enable = min(i for i, n in enumerate(self.names) if n.startswith("enable "))
        configure = self.names.index("configure linux-server")
        self.assertLess(register, first_enable)
        self.assertLess(first_enable, configure)

    def test_the_engine_cli_is_used_not_a_bare_o3de(self):
        self.assertTrue(self.steps[0].command[0].endswith("scripts/o3de.sh"))

    def test_enable_gem_uses_the_documented_flags(self):
        """-gn and -pp, as project/Code/enabled_gems.cmake itself instructs."""
        step = next(s for s in self.steps if s.name == "enable PhoenixCore")
        self.assertEqual(
            step.command[1:],
            ["enable-gem", "-gn", "PhoenixCore", "-pp", str(bringup.PROJECT)],
        )

    def test_every_step_states_why_it_exists(self):
        for step in self.steps:
            with self.subTest(step=step.name):
                self.assertGreater(len(step.why), 20)

    def test_no_configure_step_without_a_preset(self):
        names = [s.name for s in bringup.plan(healthy(), None)]
        self.assertFalse(any(n.startswith("configure") for n in names))


class DiagnosisTests(unittest.TestCase):
    def test_known_failures_are_translated(self):
        cases = {
            "ERROR: Could not find an engine": "registered O3DE engine",
            "cmake: No space left on device": "Out of disk",
            "bash: ./scripts/o3de.sh: Permission denied": "not executable",
            "project.json compatible_engines mismatch": "o3de==26.05.0",
            "CMake Error: Could not find package Foo": "3rdParty",
        }
        for output, expected in cases.items():
            with self.subTest(output=output):
                diagnosis = bringup.diagnose(output)
                self.assertIsNotNone(diagnosis, f"no diagnosis for {output!r}")
                self.assertIn(expected, diagnosis)

    def test_an_unknown_failure_returns_none_rather_than_a_wrong_guess(self):
        """A confident wrong cause sends the next hour in the wrong direction."""
        self.assertIsNone(bringup.diagnose("something nobody has seen before"))

    def test_matching_ignores_case(self):
        self.assertIsNotNone(bringup.diagnose("NO SPACE LEFT ON DEVICE"))

    def test_already_registered_is_recognised_as_benign(self):
        self.assertIn("idempotent", bringup.diagnose("Engine is already registered"))


class PersistentRootTests(unittest.TestCase):
    def test_the_most_specific_candidate_wins(self):
        present = {"/teamspace/studios/this_studio", "/teamspace"}
        self.assertEqual(
            bringup.find_persistent_root(exists=lambda p: p in present),
            "/teamspace/studios/this_studio",
        )

    def test_a_later_candidate_is_used_when_the_first_is_absent(self):
        self.assertEqual(
            bringup.find_persistent_root(exists=lambda p: p == "/workspace"),
            "/workspace",
        )

    def test_none_when_no_candidate_exists(self):
        self.assertIsNone(bringup.find_persistent_root(exists=lambda p: False))

    def test_lightning_ai_studio_path_is_a_candidate(self):
        """The machine this was written for."""
        self.assertIn("/teamspace/studios/this_studio", bringup.PERSISTENT_CANDIDATES)


class GemActivationTests(unittest.TestCase):
    def test_nothing_is_enabled_in_the_repository_today(self):
        """The fact most likely to waste the next session.

        enabled_gems.cmake is a comment and nothing else. A cmake configure
        run now succeeds and builds a project containing no Phoenix code,
        which looks like progress. If this test ever starts failing because
        gems are listed, that is good news and the assertion should be
        inverted deliberately.
        """
        enabled, missing = bringup.verify_gems_enabled()
        self.assertEqual(enabled, [])
        self.assertEqual(sorted(missing), sorted(gem.name for gem in gem_dirs()))

    def test_comments_are_not_mistaken_for_activation(self):
        """The file's own comment names 'enable-gem' and a <GemName> placeholder."""
        text = (
            bringup.PROJECT / "Code" / "enabled_gems.cmake"
        ).read_text(encoding="utf-8")
        self.assertIn("#", text)
        self.assertNotIn("PhoenixCore", text.split("#")[0])


class ReportTests(unittest.TestCase):
    def test_the_report_carries_the_facts_verdicts_and_output(self):
        facts = healthy()
        facts.gpu = "Tesla T4"
        verdicts = bringup.classify(facts, 120, 16)
        records = [
            {
                "step": "configure linux-server",
                "command": "cmake --preset linux-server",
                "status": "failed",
                "returncode": 1,
                "output": "CMake Error: Could not find package Foo",
                "diagnosis": "a 3rdParty download is missing",
            }
        ]
        text = bringup.render_report(facts, verdicts, records)
        # The machine's facts, so the report stands alone when read elsewhere.
        self.assertIn("Tesla T4", text)
        self.assertIn("engine_cli", text)
        self.assertIn("/teamspace/studios/this_studio/o3de/scripts/o3de.sh", text)
        # The verdict, so a warning is not lost between probe and report.
        self.assertIn("compiling uses none of it", text)
        # The failure, verbatim, which is the whole point of the file.
        self.assertIn("configure linux-server", text)
        self.assertIn("Could not find package Foo", text)
        self.assertIn("3rdParty download is missing", text)

    def test_an_empty_run_still_produces_a_readable_report(self):
        """--probe-only writes one too, and it must not look broken."""
        text = bringup.render_report(healthy(), [], [])
        self.assertIn("## Verdicts", text)
        self.assertIn("- none", text)
        self.assertIn("- none run", text)

    def test_it_lists_the_engine_gems_that_should_appear(self):
        text = bringup.render_report(healthy(), [], [])
        for gem in ("PhysX5", "RecastNavigation", "SaveData", "Atom"):
            with self.subTest(gem=gem):
                self.assertIn(gem, text)

    def test_the_expected_engine_gems_match_the_manifests(self):
        """So the report cannot claim a dependency set the gems do not declare."""
        import json

        declared = set()
        for gem in gem_dirs():
            document = json.loads((gem / "gem.json").read_text(encoding="utf-8"))
            declared.update(
                d for d in document.get("dependencies", []) if not d.startswith("Phoenix")
            )
        self.assertEqual(set(bringup.EXPECTED_ENGINE_GEMS), declared)


class ProbeTests(unittest.TestCase):
    def test_the_probe_runs_here_and_measures_something(self):
        facts = bringup.probe()
        self.assertEqual(facts.system, "Linux")
        self.assertIsNotNone(facts.cpu_count)
        self.assertIsNotNone(facts.free_gb)
        self.assertIsNotNone(facts.python)

    def test_an_absent_engine_is_none_not_a_guess(self):
        """No searching likely directories: a wrong engine is worse than none."""
        facts = bringup.probe(engine=None)
        self.assertIsNone(facts.engine_cli)

    def test_an_explicit_engine_path_without_the_cli_yields_no_cli(self):
        engine, cli = bringup.find_engine("/definitely/not/an/engine")
        self.assertTrue(engine.endswith("not/an/engine"))
        self.assertIsNone(cli)


if __name__ == "__main__":
    unittest.main()


class MainPathTests(unittest.TestCase):
    """The closest thing to an end-to-end test this environment allows.

    --probe-only exercises argument parsing, the probe, the verdict rules, the
    console output and the report writer in one process. It cannot reach the
    engine steps, but it proves the script runs rather than dying on an import
    or a typo in main() -- which is the failure that would waste the first
    five minutes of the session it was written for.
    """

    def test_probe_only_runs_and_writes_its_report(self):
        import json
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(ROOT / "scripts" / "bringup.py"),
                    "--probe-only",
                    "--report",
                    str(report),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            # Exit 1 is correct here: this container has no engine, which is a
            # blocker. A 0 would mean the blocker rules had stopped working.
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("BLOCKER", result.stdout)
            self.assertIn("engine", result.stdout)
            self.assertIn("Probe only; nothing was changed.", result.stdout)
            self.assertTrue(report.is_file(), "no report was written")
            text = report.read_text(encoding="utf-8")
            self.assertIn("## Machine", text)
            self.assertIn("## Verdicts", text)
            del json

    def test_dry_run_prints_every_command_without_running_one(self):
        """So the plan can be reviewed before anything touches the machine."""
        import subprocess
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.md"
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(ROOT / "scripts" / "bringup.py"),
                    "--engine",
                    "/definitely/not/an/engine",
                    "--dry-run",
                    "--force",
                    "--report",
                    str(report),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
        self.assertIn("(dry run, not executed)", output)
        self.assertIn("enable-gem", output)
        for gem in gem_dirs():
            with self.subTest(gem=gem.name):
                self.assertIn(gem.name, output)
        self.assertNotIn("Traceback", output)

    def test_it_is_not_wired_into_ci(self):
        """It needs an engine, so in CI it would fail on every run.

        Stated as a test because the opposite mistake -- adding it to a
        workflow for completeness -- would turn every pull request red for a
        reason that has nothing to do with the change.
        """
        workflows = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        )
        self.assertNotIn("bringup.py", workflows)
