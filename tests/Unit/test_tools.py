import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT

TOOLS = ROOT / "tools"


def run_tool(relative, *args):
    return subprocess.run(
        [sys.executable, str(TOOLS / relative), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class ToolsPassOnTheCommittedTreeTests(unittest.TestCase):
    """The tools must hold against the tree they ship with."""

    def test_validate_project(self):
        result = run_tool("validation/validate_project.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validate_assets(self):
        result = run_tool("validation/validate_assets.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_analyze_budget(self):
        result = run_tool("profiling/analyze_budget.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class SaveMigrationTests(unittest.TestCase):
    """docs/tdd/06 requires migrations to be deterministic and tested."""

    def setUp(self):
        sys.path.insert(0, str(TOOLS / "migration"))
        import migrate_save

        self.migrate_save = migrate_save

    def test_v1_migrates_to_current(self):
        source = json.loads(
            (ROOT / "tests" / "data" / "saves" / "campaign_v1.json").read_text(
                encoding="utf-8"
            )
        )
        expected = json.loads(
            (ROOT / "tests" / "data" / "saves" / "campaign_v2.json").read_text(
                encoding="utf-8"
            )
        )
        migrated, applied = self.migrate_save.migrate(source)
        self.assertEqual(applied, ["v1 -> v2"])
        self.assertEqual(migrated, expected)

    def test_migration_is_deterministic(self):
        source = json.loads(
            (ROOT / "tests" / "data" / "saves" / "campaign_v1.json").read_text(
                encoding="utf-8"
            )
        )
        first, _ = self.migrate_save.migrate(json.loads(json.dumps(source)))
        second, _ = self.migrate_save.migrate(json.loads(json.dumps(source)))
        self.assertEqual(first, second)

    def test_migration_does_not_mutate_its_input(self):
        source = json.loads(
            (ROOT / "tests" / "data" / "saves" / "campaign_v1.json").read_text(
                encoding="utf-8"
            )
        )
        snapshot = json.loads(json.dumps(source))
        self.migrate_save.migrate(source)
        self.assertEqual(source, snapshot, "migrate() must be pure")

    def test_current_version_is_a_noop(self):
        current = {"schemaVersion": self.migrate_save.CURRENT_SCHEMA_VERSION}
        migrated, applied = self.migrate_save.migrate(current)
        self.assertEqual(applied, [])
        self.assertEqual(migrated, current)

    def test_newer_save_is_refused(self):
        future = {"schemaVersion": self.migrate_save.CURRENT_SCHEMA_VERSION + 1}
        with self.assertRaises(ValueError) as caught:
            self.migrate_save.migrate(future)
        self.assertIn("newer than this build", str(caught.exception))

    def test_missing_version_is_refused(self):
        with self.assertRaises(ValueError):
            self.migrate_save.migrate({"campaign": {}})

    def test_migration_chain_has_no_gaps(self):
        """Every version below current must have a registered migration."""
        for version in range(1, self.migrate_save.CURRENT_SCHEMA_VERSION):
            with self.subTest(version=version):
                self.assertIn(version, self.migrate_save.MIGRATIONS)


class BudgetAnalysisTests(unittest.TestCase):
    def test_exceeded_budget_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            measurements = Path(tmp) / "m.json"
            # The client frame target is 16.67 ms; 25 ms must fail.
            measurements.write_text(
                json.dumps({"client.frame": {"targetMs": 25.0}}), encoding="utf-8"
            )
            result = run_tool(
                "profiling/analyze_budget.py", "--measurements", str(measurements)
            )
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("exceeded", result.stderr)

    def test_within_budget_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            measurements = Path(tmp) / "m.json"
            measurements.write_text(
                json.dumps({"client.frame": {"targetMs": 14.0}}), encoding="utf-8"
            )
            result = run_tool(
                "profiling/analyze_budget.py", "--measurements", str(measurements)
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_require_all_set_fails_while_budgets_are_open(self):
        """Most budgets are deliberately unset; the strict gate must say so."""
        result = run_tool("profiling/analyze_budget.py", "--require-all-set")
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("still unset", result.stderr)


if __name__ == "__main__":
    unittest.main()


class EveryToolIsRunAndListedTests(unittest.TestCase):
    """A tool nobody runs is not a gate. A tool nobody lists is not findable.

    Both failures are quiet. A validator added to tools/ but never wired into
    a workflow passes forever by never executing, and the next person reads
    its name in CONTRIBUTING and assumes it is enforced. A tool missing from
    tools/README.md still runs, but nobody learns it exists until they
    duplicate it.

    These checks discover the tool set from disk rather than from a list kept
    here, so a tool added tomorrow is covered without anyone remembering to
    extend this file.
    """

    #: Tools that deliberately do not run in CI, each with the reason. Keeping
    #: this empty-by-default and explicit is the point: an exemption has to be
    #: argued in a diff rather than achieved by forgetting.
    NOT_IN_CI: dict[str, str] = {
        "migration/migrate_save.py": (
            "operates on a save file supplied by the caller; it has no repository-wide "
            "invocation. Its behaviour is covered by SaveMigrationTests above."
        ),
    }

    def tools(self) -> list[str]:
        found = []
        for path in sorted(TOOLS.rglob("*.py")):
            if "__pycache__" in path.parts or path.name.startswith("_"):
                continue
            found.append(path.relative_to(TOOLS).as_posix())
        return found

    def test_there_are_tools_to_check(self):
        """Guards the three tests below against an empty discovery."""
        self.assertGreaterEqual(len(self.tools()), 8)

    def test_every_tool_runs_clean_on_the_committed_tree(self):
        for relative in self.tools():
            if relative in self.NOT_IN_CI:
                continue
            with self.subTest(tool=relative):
                result = run_tool(relative)
                self.assertEqual(
                    result.returncode, 0, (result.stdout + result.stderr)[:3000]
                )

    def test_every_tool_is_listed_in_the_readme(self):
        text = (TOOLS / "README.md").read_text(encoding="utf-8")
        for relative in self.tools():
            with self.subTest(tool=relative):
                self.assertIn(
                    relative,
                    text,
                    f"tools/{relative} is not in tools/README.md; add a row describing "
                    "what it does",
                )

    def test_every_tool_is_invoked_by_a_workflow(self):
        workflows = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        )
        for relative in self.tools():
            with self.subTest(tool=relative):
                if relative in self.NOT_IN_CI:
                    self.assertTrue(
                        self.NOT_IN_CI[relative].strip(),
                        "an exemption needs a reason",
                    )
                    continue
                self.assertIn(
                    f"tools/{relative}",
                    workflows,
                    f"tools/{relative} is in no workflow, so it never runs. A validator "
                    "that never executes passes forever and reads as coverage",
                )

    def test_the_readme_does_not_claim_a_count_that_can_drift(self):
        """'All four run' was true once. Counts in prose go stale silently."""
        text = (TOOLS / "README.md").read_text(encoding="utf-8")
        count = len(self.tools())
        words = {
            4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
            10: "ten", 11: "eleven", 12: "twelve",
        }
        for number, word in words.items():
            if number == count:
                continue
            with self.subTest(claim=word):
                self.assertNotIn(
                    f"All {word} run",
                    text,
                    f"tools/README.md claims 'All {word} run' but there are {count} tools",
                )


class ContributingListsEveryLocalCheckTests(unittest.TestCase):
    """CONTRIBUTING tells contributors what to run before opening a PR.

    When it falls behind, the cost lands on the contributor: they run the five
    commands the file lists, open the PR, and CI fails on the sixth. The file
    said "All three run in CI" while listing six commands, which is how this
    test came to exist.
    """

    def contributing(self) -> str:
        return (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    def test_it_lists_every_tool_ci_runs(self):
        text = self.contributing()
        exempt = EveryToolIsRunAndListedTests.NOT_IN_CI
        for path in sorted(TOOLS.rglob("*.py")):
            if "__pycache__" in path.parts or path.name.startswith("_"):
                continue
            relative = path.relative_to(TOOLS).as_posix()
            if relative in exempt:
                continue
            with self.subTest(tool=relative):
                self.assertIn(
                    f"tools/{relative}",
                    text,
                    f"CONTRIBUTING.md does not tell contributors to run "
                    f"tools/{relative}, so they will learn about it from a red CI run",
                )

    def test_it_lists_every_repository_script_ci_runs(self):
        text = self.contributing()
        for script in ("validate.py", "check_architecture.py", "check_cmake.py", "test.py"):
            with self.subTest(script=script):
                self.assertIn(f"scripts/{script}", text)

    def test_it_mentions_the_format_check(self):
        self.assertIn("clang-format", self.contributing())

    def test_it_claims_no_count_that_can_drift(self):
        """'All three run in CI' was the original wording, with six listed."""
        text = self.contributing()
        for word in ("All three run", "All four run", "All five run", "All six run"):
            with self.subTest(claim=word):
                self.assertNotIn(word, text)
