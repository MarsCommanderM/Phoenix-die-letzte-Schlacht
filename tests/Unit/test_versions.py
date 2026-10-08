import contextlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT, load_json

sys.path.insert(0, str(ROOT / "tools" / "migration"))
sys.path.insert(0, str(ROOT / "tools" / "validation"))

import migrate_save  # noqa: E402
import validate_versions  # noqa: E402

CONFIG = ROOT / "project" / "Config"
VALIDATOR = ROOT / "tools" / "validation" / "validate_versions.py"


def good_documents() -> dict[str, dict]:
    """A set of contract documents that must validate.

    Built from the code rather than hardcoded, so these fixtures cannot be the
    thing that drifts.
    """
    return {
        "version.json": {"product": "Phoenix", "major": 0, "minor": 1, "patch": 0},
        "network_protocol.json": {
            "protocol": 1,
            "minimumCompatible": 1,
            "maximumCompatible": 1,
        },
        "save_schema.json": {
            "current": migrate_save.CURRENT_SCHEMA_VERSION,
            "minimumReadable": min(migrate_save.MIGRATIONS),
        },
    }


@contextlib.contextmanager
def candidate_config(overrides: dict):
    """A throwaway config directory, valid except where an override breaks it.

    The failure cases run against a temporary directory instead of editing
    project/Config, because a check that can only be exercised by breaking the
    committed tree is a check nobody runs.

    An override value of None omits that file; a string is written verbatim so
    a malformed-JSON case can be expressed.
    """
    documents = good_documents()
    documents.update(overrides)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        for name, document in documents.items():
            if document is None:
                continue
            text = (
                document
                if isinstance(document, str)
                else json.dumps(document, indent=4) + "\n"
            )
            (directory / name).write_text(text, encoding="utf-8")
        yield directory


def problems(overrides: dict) -> list[str]:
    with candidate_config(overrides) as directory:
        errors, _ = validate_versions.validate(directory)
    return errors


class CommittedContractsTests(unittest.TestCase):
    """v5.1 sections 251-253: three contracts, each versioned on its own line."""

    def test_validator_passes_on_the_committed_tree(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # A gate that cannot report what it covered cannot be trusted.
        self.assertIn("3 contract files", result.stdout)
        self.assertIn("8 integer fields checked", result.stdout)

    def test_product_version(self):
        document = load_json(CONFIG / "version.json")
        self.assertEqual(document["product"], "Phoenix")
        self.assertEqual(
            (document["major"], document["minor"], document["patch"]), (0, 1, 0)
        )

    def test_network_protocol(self):
        document = load_json(CONFIG / "network_protocol.json")
        self.assertEqual(document["protocol"], 1)
        self.assertEqual(document["minimumCompatible"], 1)
        self.assertEqual(document["maximumCompatible"], 1)

    def test_save_schema_agrees_with_the_migration_code(self):
        """The config must not claim a version the migration chain cannot write."""
        document = load_json(CONFIG / "save_schema.json")
        self.assertEqual(document["current"], migrate_save.CURRENT_SCHEMA_VERSION)
        self.assertEqual(document["minimumReadable"], 1)

    def test_declared_readable_range_is_reachable(self):
        document = load_json(CONFIG / "save_schema.json")
        for version in range(document["minimumReadable"], document["current"]):
            with self.subTest(version=version):
                self.assertIn(version, migrate_save.MIGRATIONS)

    def test_each_contract_explains_itself(self):
        """Section 26.5: the independence of these lines is the point, so it is written down."""
        for name in ("version.json", "network_protocol.json", "save_schema.json"):
            with self.subTest(name=name):
                comment = load_json(CONFIG / name)["$comment"]
                self.assertIn("independently", comment)
                self.assertIn("different rates", comment)


class CandidateConfigIsAcceptedTests(unittest.TestCase):
    def test_a_valid_candidate_has_no_problems(self):
        self.assertEqual(problems({}), [])


class MalformedContractsAreRejectedTests(unittest.TestCase):
    def assertProblem(self, overrides: dict, fragment: str):
        found = problems(overrides)
        self.assertTrue(found, f"expected a problem for {overrides!r}")
        self.assertTrue(
            any(fragment in problem for problem in found),
            f"no problem mentioned {fragment!r}; got {found!r}",
        )

    def test_missing_file(self):
        self.assertProblem({"save_schema.json": None}, "missing")

    def test_unparseable_file(self):
        self.assertProblem({"version.json": "{ not json"}, "invalid JSON")

    def test_non_object_top_level(self):
        self.assertProblem({"version.json": "[1, 2, 3]"}, "JSON object")

    def test_missing_integer_field(self):
        self.assertProblem(
            {"version.json": {"product": "Phoenix", "major": 0, "minor": 1}},
            "'patch' must be an integer",
        )

    def test_non_integer_field(self):
        self.assertProblem(
            {
                "network_protocol.json": {
                    "protocol": "1",
                    "minimumCompatible": 1,
                    "maximumCompatible": 1,
                }
            },
            "'protocol' must be an integer",
        )

    def test_boolean_is_not_an_integer(self):
        """JSON true parses to a bool, and bool subclasses int."""
        self.assertProblem(
            {
                "network_protocol.json": {
                    "protocol": True,
                    "minimumCompatible": 1,
                    "maximumCompatible": 1,
                }
            },
            "'protocol' must be an integer",
        )

    def test_empty_product_name(self):
        self.assertProblem(
            {"version.json": {"product": "  ", "major": 0, "minor": 1, "patch": 0}},
            "'product' must be a non-empty string",
        )


class CompatibilityWindowTests(unittest.TestCase):
    def test_protocol_below_minimum_compatible(self):
        found = problems(
            {
                "network_protocol.json": {
                    "protocol": 1,
                    "minimumCompatible": 2,
                    "maximumCompatible": 3,
                }
            }
        )
        self.assertTrue(any("excludes itself" in problem for problem in found), found)

    def test_protocol_above_maximum_compatible(self):
        found = problems(
            {
                "network_protocol.json": {
                    "protocol": 4,
                    "minimumCompatible": 1,
                    "maximumCompatible": 3,
                }
            }
        )
        self.assertTrue(any("excludes itself" in problem for problem in found), found)

    def test_a_wider_window_is_allowed(self):
        """Accepting a range of peers is normal; only excluding yourself is not."""
        self.assertEqual(
            problems(
                {
                    "network_protocol.json": {
                        "protocol": 2,
                        "minimumCompatible": 1,
                        "maximumCompatible": 3,
                    }
                }
            ),
            [],
        )


class SaveSchemaAgreementTests(unittest.TestCase):
    def test_current_ahead_of_the_migration_chain(self):
        found = problems(
            {
                "save_schema.json": {
                    "current": migrate_save.CURRENT_SCHEMA_VERSION + 1,
                    "minimumReadable": 1,
                }
            }
        )
        self.assertTrue(
            any("migrate_save.py" in problem for problem in found), found
        )

    def test_current_behind_the_migration_chain(self):
        found = problems(
            {
                "save_schema.json": {
                    "current": migrate_save.CURRENT_SCHEMA_VERSION - 1,
                    "minimumReadable": 1,
                }
            }
        )
        self.assertTrue(
            any("migrate_save.py" in problem for problem in found), found
        )

    def test_minimum_readable_above_current(self):
        found = problems(
            {
                "save_schema.json": {
                    "current": migrate_save.CURRENT_SCHEMA_VERSION,
                    "minimumReadable": migrate_save.CURRENT_SCHEMA_VERSION + 1,
                }
            }
        )
        self.assertTrue(
            any("is above current" in problem for problem in found), found
        )

    def test_unreachable_readable_range(self):
        """Claiming to read v0 needs a v0 -> v1 migration that does not exist."""
        found = problems(
            {
                "save_schema.json": {
                    "current": migrate_save.CURRENT_SCHEMA_VERSION,
                    "minimumReadable": 0,
                }
            }
        )
        self.assertTrue(
            any("no migration from v0" in problem for problem in found), found
        )


if __name__ == "__main__":
    unittest.main()
