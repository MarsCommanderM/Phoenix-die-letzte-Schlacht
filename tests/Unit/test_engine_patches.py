"""The engine patch register, and proof its per-patch rules work.

The register is empty, which is the point: the fork is identical to the
pinned engine. It is also the problem for testing. A validator whose
per-entry rules have never once run against an entry has not been shown to
work, and the first real engine patch is the worst moment to find out that
the gate guarding it does nothing.

So every rule is exercised against a synthetic patch file, written into the
real directory and removed again in a finally block.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "validation"))

import validate_engine_patches as patches  # noqa: E402

PATCH_DIR = ROOT / "docs" / "engine-patches"
REGISTER = PATCH_DIR / "README.md"
TEMPLATE = PATCH_DIR / "TEMPLATE.md"

GOOD_PATCH = """# EP-0001 Fix a thing

Status: carried
Owner: Engineering
ADR: ../adr/0009-engine-fork-policy.md
Engine version: 26.05.0
Category: engine-bug
Upstream issue: https://github.com/o3de/o3de/issues/1
Dropped in: n/a

## What the patch changes

One file.

## Why this cannot live in a Phoenix gem

It is below the gem boundary.

## Rebase cost

Small.

## Exit condition

Upstream fix ships.
"""

ROW = "| [0001](0001-fix-a-thing.md) | Fix a thing | engine-bug | Engineering | 26.05.0 | carried |\n"


class PatchFixture(unittest.TestCase):
    """Writes synthetic patch files and always puts the directory back."""

    def run_with(self, body: str, *, name: str = "0001-fix-a-thing.md", row: str | None = None):
        path = PATCH_DIR / name
        original = REGISTER.read_text(encoding="utf-8")
        self.assertFalse(path.exists(), f"{name} already exists; test would clobber it")
        try:
            path.write_text(body, encoding="utf-8")
            if row is not None:
                REGISTER.write_text(
                    original.replace(
                        "| --- | --- | --- | --- | --- | --- |\n",
                        "| --- | --- | --- | --- | --- | --- |\n" + row,
                    ),
                    encoding="utf-8",
                )
            errors, stats = patches.validate()
        finally:
            path.unlink(missing_ok=True)
            REGISTER.write_text(original, encoding="utf-8")
        return errors, stats

    def assertRejects(self, fragment: str, body: str, **kwargs):
        errors, _ = self.run_with(body, **kwargs)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected a failure mentioning {fragment!r}; got: {errors}",
        )


class EmptyRegisterTests(unittest.TestCase):
    def test_the_register_and_template_exist(self):
        self.assertTrue(REGISTER.is_file(), "docs/engine-patches/README.md is missing")
        self.assertTrue(TEMPLATE.is_file(), "docs/engine-patches/TEMPLATE.md is missing")

    def test_it_passes_today(self):
        errors, stats = patches.validate()
        self.assertEqual(errors, [], f"register does not validate: {errors}")
        self.assertEqual(stats["patches"], 0)
        self.assertEqual(stats["rows"], 0)

    def test_the_template_carries_every_field_it_demands(self):
        text = TEMPLATE.read_text(encoding="utf-8")
        for name in patches.REQUIRED_FIELDS:
            with self.subTest(field=name):
                self.assertIsNotNone(patches.field(text, name))
        for section in patches.REQUIRED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(f"## {section}", text)

    def test_the_register_states_the_set_is_empty_rather_than_omitting_it(self):
        """An empty table is a checked zero; an absent file is an unanswered question."""
        text = REGISTER.read_text(encoding="utf-8")
        self.assertIn("**None.**", text)
        self.assertIn("| Patch | Title | Category | Owner | Engine version | Status |", text)

    def test_the_register_links_the_policy_adr(self):
        self.assertIn("0009-engine-fork-policy.md", REGISTER.read_text(encoding="utf-8"))


class PatchRuleTests(PatchFixture):
    def test_a_well_formed_patch_with_a_row_is_accepted(self):
        """The positive case, so the rejections below mean something."""
        errors, stats = self.run_with(GOOD_PATCH, row=ROW)
        self.assertEqual(errors, [], f"a valid patch was rejected: {errors}")
        self.assertEqual(stats["patches"], 1)
        self.assertEqual(stats["carried"], 1)
        self.assertEqual(stats["rows"], 1)

    def test_a_patch_absent_from_the_register_is_rejected(self):
        """The liability nobody counts."""
        self.assertRejects("is not in the table", GOOD_PATCH)

    def test_a_dropped_patch_may_leave_the_table(self):
        body = GOOD_PATCH.replace("Status: carried", "Status: dropped").replace(
            "Dropped in: n/a", "Dropped in: 26.10.0"
        )
        errors, stats = self.run_with(body)
        self.assertEqual(errors, [], errors)
        self.assertEqual(stats["carried"], 0)

    def test_a_dropped_patch_must_name_the_version_that_ended_it(self):
        body = GOOD_PATCH.replace("Status: carried", "Status: dropped")
        self.assertRejects("the engine version that ended the patch", body)

    def test_a_drop_version_without_dropped_status_is_rejected(self):
        body = GOOD_PATCH.replace("Dropped in: n/a", "Dropped in: 26.10.0")
        self.assertRejects("a patch", body, row=ROW)

    def test_an_unreported_upstream_issue_is_rejected(self):
        """A patch with no exit condition is carried forever by construction."""
        body = GOOD_PATCH.replace(
            "Upstream issue: https://github.com/o3de/o3de/issues/1",
            "Upstream issue: not reported",
        )
        self.assertRejects("no exit condition", body, row=ROW)

    def test_none_with_a_place_it_was_reported_is_accepted(self):
        body = GOOD_PATCH.replace(
            "Upstream issue: https://github.com/o3de/o3de/issues/1",
            "Upstream issue: none - raised on the o3de Discord #sig-core, 2026-10-01",
        )
        errors, _ = self.run_with(body, row=ROW)
        self.assertEqual(errors, [], errors)

    def test_a_category_outside_adr_0009_is_rejected(self):
        body = GOOD_PATCH.replace("Category: engine-bug", "Category: convenience")
        self.assertRejects("five admissible reasons", body, row=ROW)

    def test_an_empty_required_field_is_rejected(self):
        body = GOOD_PATCH.replace("Owner: Engineering", "Owner:")
        self.assertRejects("'Owner' is empty", body, row=ROW)

    def test_a_missing_section_is_rejected(self):
        body = GOOD_PATCH.replace("## Rebase cost", "## Notes")
        self.assertRejects("## Rebase cost", body, row=ROW)

    def test_an_adr_that_does_not_resolve_is_rejected(self):
        body = GOOD_PATCH.replace(
            "ADR: ../adr/0009-engine-fork-policy.md", "ADR: ../adr/9999-nonexistent.md"
        )
        self.assertRejects("does not resolve", body, row=ROW)

    def test_a_badly_named_file_is_rejected(self):
        self.assertRejects(
            "NNNN-slug.md", GOOD_PATCH, name="EnginePatch_One.md"
        )

    def test_an_unknown_status_is_rejected(self):
        body = GOOD_PATCH.replace("Status: carried", "Status: maybe")
        self.assertRejects("is not one of", body, row=ROW)

    def test_a_register_row_without_a_file_is_rejected(self):
        """The other direction: a row left behind after a drop."""
        original = REGISTER.read_text(encoding="utf-8")
        try:
            REGISTER.write_text(
                original.replace(
                    "| --- | --- | --- | --- | --- | --- |\n",
                    "| --- | --- | --- | --- | --- | --- |\n" + ROW,
                ),
                encoding="utf-8",
            )
            errors, _ = patches.validate()
        finally:
            REGISTER.write_text(original, encoding="utf-8")
        self.assertTrue(any("has no file" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
