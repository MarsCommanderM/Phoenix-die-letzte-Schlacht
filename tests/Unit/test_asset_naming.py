"""The asset naming gate, and proof that each of its rules can fail.

No production asset is authored yet, so the prefix rules have nothing in the
tree to reject. That is exactly the condition under which a naming validator
becomes decoration: it prints "passed" forever because it never looks at
anything. Every rule therefore gets a negative test with a synthetic path, so
the gate is proven to work before there is content for it to work on.

The documentation is tested too. docs/production/naming.md promises that its
prefix table and the validator's PRODUCTION_PREFIXES change together; this is
what makes that promise true rather than aspirational.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "validation"))

import validate_asset_naming as naming  # noqa: E402

NAMING_DOC = ROOT / "docs" / "production" / "naming.md"


class SyntheticTree:
    """Replaces iter_source_files() with a fixed list of paths under ROOT.

    The checks walk the repository, so a negative test either writes files
    into the working tree or substitutes the walk. Substituting it keeps the
    tests from leaving debris behind when one of them fails.
    """

    def __init__(self, *relatives: str):
        self.paths = [ROOT / relative for relative in relatives]
        self.original = None

    def __enter__(self):
        self.original = naming.iter_source_files
        naming.iter_source_files = lambda: iter(self.paths)
        return self

    def __exit__(self, *exc):
        naming.iter_source_files = self.original
        return False


def errors_from(check, *relatives: str) -> list[str]:
    errors: list[str] = []
    with SyntheticTree(*relatives):
        check(errors)
    return errors


class CommittedTreeTests(unittest.TestCase):
    def test_the_repository_passes(self):
        errors, _ = naming.validate()
        self.assertEqual(errors, [], f"committed tree violates its own naming rules: {errors}")

    def test_it_reports_how_much_it_actually_checked(self):
        """A count is what separates a gate from a rubber stamp."""
        _, stats = naming.validate()
        self.assertGreater(stats["paths"], 50)
        self.assertGreater(stats["governed"], 50)
        self.assertEqual(stats["data"], 3)
        self.assertEqual(sum(stats["production"].values()), 0)


class CaseCollisionTests(unittest.TestCase):
    def test_paths_differing_only_by_case_are_rejected(self):
        """The Linux-server failure: resolves on Windows, fails in production."""
        errors = errors_from(
            naming.check_case_collisions,
            "project/Assets/Textures/T_Rock_BaseColor.png",
            "project/Assets/Textures/t_rock_basecolor.png",
        )
        self.assertTrue(any("differ only by case" in e for e in errors), errors)

    def test_distinct_paths_are_accepted(self):
        errors = errors_from(
            naming.check_case_collisions,
            "project/Assets/Textures/T_Rock_BaseColor.png",
            "project/Assets/Textures/T_Rock_Normal.png",
        )
        self.assertEqual(errors, [])


class PathCharacterTests(unittest.TestCase):
    def test_a_space_is_rejected(self):
        errors = errors_from(
            naming.check_path_characters, "project/Assets/Textures/T_Rock Cliff.png"
        )
        self.assertTrue(any("outside" in e for e in errors), errors)

    def test_an_accented_character_is_rejected(self):
        errors = errors_from(
            naming.check_path_characters, "project/Assets/Textures/T_Hoehle.png".replace("oe", "ö")
        )
        self.assertTrue(any("outside" in e for e in errors), errors)

    def test_status_suffixes_are_rejected(self):
        for suffix in ("_final", "_old", "_copy", "_wip", "_tmp", "_backup"):
            with self.subTest(suffix=suffix):
                errors = errors_from(
                    naming.check_path_characters,
                    f"project/Assets/Textures/T_Rock{suffix}.png",
                )
                self.assertTrue(any(suffix in e for e in errors), errors)

    def test_a_numbered_revision_is_rejected(self):
        errors = errors_from(
            naming.check_path_characters, "project/Assets/Textures/T_Rock_v2.png"
        )
        self.assertTrue(any("numbered revision" in e for e in errors), errors)

    def test_ungoverned_paths_are_skipped(self):
        """Python and docs follow their own conventions, and dotfiles are tools'."""
        errors = errors_from(
            naming.check_path_characters,
            "scripts/check_cmake.py",
            "tests/Unit/test_tools.py",
            "docs/tdd/90-source-reconciliation.md",
            ".clang-format",
        )
        self.assertEqual(errors, [])


class ProductionAssetTests(unittest.TestCase):
    def test_a_missing_prefix_is_rejected(self):
        errors = errors_from(
            naming.check_production_assets, "project/Assets/Textures/RockCliff.png"
        )
        self.assertTrue(any("must start with one of" in e for e in errors), errors)

    def test_a_lowercase_body_is_rejected(self):
        errors = errors_from(
            naming.check_production_assets, "project/Assets/Textures/T_rock_cliff.png"
        )
        self.assertTrue(any("PascalCase" in e for e in errors), errors)

    def test_each_declared_prefix_accepts_a_correct_name(self):
        """Every rule in the table is exercised, not just the two above."""
        samples = {
            "T_": "project/Assets/Textures/T_RockCliff_BaseColor.png",
            "M_": "project/Assets/Materials/M_RockCliff.material",
            "SM_": "project/Assets/Meshes/SM_RockCliff.fbx",
            "SK_": "project/Assets/Meshes/SK_CharacterBase.fbx",
            "A_": "project/Assets/Animations/A_CharacterRun.motion",
            "P_": "project/Assets/Prefabs/P_SupplyCrate.prefab",
            "S_": "project/Assets/Sounds/S_FootstepMetal.wav",
            "L_": "project/Levels/L_TrainingGround.prefab",
        }
        self.assertEqual(
            sorted(samples), sorted(naming.PRODUCTION_PREFIXES),
            "a prefix was added to the validator without a sample here",
        )
        for prefix, path in samples.items():
            with self.subTest(prefix=prefix):
                errors: list[str] = []
                with SyntheticTree(path):
                    counts = naming.check_production_assets(errors)
                self.assertEqual(errors, [])
                # .fbx and .prefab are shared, so only assert something matched.
                self.assertEqual(sum(counts.values()), 1)

    def test_shared_extensions_accept_any_of_their_prefixes(self):
        """.fbx is SM_, SK_ or A_; the rule is 'one of', never 'exactly one'."""
        self.assertEqual(naming.PREFIXES_BY_EXTENSION[".fbx"], {"SM_", "SK_", "A_"})
        self.assertEqual(naming.PREFIXES_BY_EXTENSION[".prefab"], {"P_", "L_"})


class DataDocumentTests(unittest.TestCase):
    def test_a_missing_category_prefix_is_rejected(self):
        """Written into the real data tree, and removed even if the check throws."""
        intruder = ROOT / "project" / "Assets" / "Data" / "Actions" / "interact.json"
        intruder.write_text('{"id": "interact"}\n', encoding="utf-8")
        try:
            errors: list[str] = []
            naming.check_data_documents(errors)
        finally:
            intruder.unlink(missing_ok=True)
        self.assertTrue(any("must start with 'action_'" in e for e in errors), errors)

    def test_an_uppercase_data_name_is_rejected(self):
        intruder = ROOT / "project" / "Assets" / "Data" / "Actions" / "action_Interact.json"
        intruder.write_text('{"id": "action_Interact"}\n', encoding="utf-8")
        try:
            errors: list[str] = []
            naming.check_data_documents(errors)
        finally:
            intruder.unlink(missing_ok=True)
        self.assertTrue(any("lower_snake_case" in e for e in errors), errors)

    def test_singular_handles_the_categories_in_use(self):
        self.assertEqual(naming.singular("Actions"), "action")
        self.assertEqual(naming.singular("Missions"), "mission")
        self.assertEqual(naming.singular("Objectives"), "objective")


class DocumentationAgreementTests(unittest.TestCase):
    def test_the_document_exists(self):
        self.assertTrue(NAMING_DOC.is_file(), "docs/production/naming.md is missing")

    def test_the_prefix_table_matches_the_validator(self):
        """The promise at the end of naming.md, enforced.

        Two places that state the same rule drift apart unless something
        compares them. This is that something.
        """
        text = NAMING_DOC.read_text(encoding="utf-8")
        documented = set(re.findall(r"^\| `([A-Z]+_)` \|", text, re.M))
        self.assertEqual(
            documented,
            set(naming.PRODUCTION_PREFIXES),
            "docs/production/naming.md and PRODUCTION_PREFIXES disagree; they are "
            "required to change in the same commit",
        )

    def test_the_document_states_why_the_rules_are_enforced(self):
        text = NAMING_DOC.read_text(encoding="utf-8")
        self.assertIn("case-sensitive on Linux", text)
        self.assertIn("tools/validation/validate_asset_naming.py", text)


if __name__ == "__main__":
    unittest.main()
