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
