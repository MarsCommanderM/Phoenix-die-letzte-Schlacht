import re
import unittest
from pathlib import Path

import sys

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT

#: Markdown links that point at a repository path, not an external URL or a
#: pure anchor.
LINK = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")

SKIP_PREFIXES = ("http://", "https://", "mailto:")


def markdown_files():
    return sorted(
        p for p in ROOT.rglob("*.md") if ".git" not in p.parts and "build" not in p.parts
    )


class DocumentationLinkTests(unittest.TestCase):
    """A 13-chapter document set cross-references heavily; dangling links rot."""

    def test_internal_links_resolve(self):
        broken = []
        for path in markdown_files():
            for match in LINK.finditer(path.read_text(encoding="utf-8")):
                target = match.group(1).strip()
                if not target or target.startswith(SKIP_PREFIXES):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {target}")
        self.assertEqual(broken, [], f"dangling links: {broken}")

    def test_tdd_chapters_are_all_indexed(self):
        tdd = ROOT / "docs" / "tdd"
        chapters = {p.name for p in tdd.glob("*.md")} - {"README.md"}
        index = (tdd / "README.md").read_text(encoding="utf-8")
        missing = sorted(c for c in chapters if c not in index)
        self.assertEqual(missing, [], f"chapters absent from the index: {missing}")

    def test_adrs_are_all_registered(self):
        adr_dir = ROOT / "docs" / "adr"
        adrs = {p.name for p in adr_dir.glob("0*.md")}
        register = (adr_dir / "README.md").read_text(encoding="utf-8")
        missing = sorted(a for a in adrs if a not in register)
        self.assertEqual(missing, [], f"ADRs absent from the register: {missing}")


if __name__ == "__main__":
    unittest.main()


class LicenceAttributionTests(unittest.TestCase):
    """NOTICE is the one file the licence makes travel with every copy.

    Apache-2.0 section 4(d) requires a derivative work to carry the NOTICE
    text. That makes its copyright line the single highest-leverage string in
    the repository and the one nobody looks at again after writing it once:
    a placeholder shipped in a release cannot be recalled from the copies
    already distributed.

    The LICENSE hash is checked here for the reason ADR-0011 states about
    itself -- a recorded hash that nothing verifies is worse than none,
    because it looks like verification. NOTICE tells the reader to run
    `sha256sum LICENSE`; this is what makes that instruction true without
    anyone having to.
    """

    #: Strings that mean "nobody has decided yet". A copyright line holding
    #: any of these is not an attribution, whatever it looks like.
    PLACEHOLDERS = (
        "the phoenix authors",
        "phoenix authors",
        "todo",
        "tbd",
        "fixme",
        "your name",
        "<name>",
        "[name]",
        "copyright holder",
        "author name",
        "company name",
        "xxx",
    )

    def setUp(self):
        self.notice = ROOT / "NOTICE"
        self.assertTrue(self.notice.is_file(), "NOTICE is missing")
        self.text = self.notice.read_text(encoding="utf-8")

    def copyright_line(self) -> str:
        match = re.search(r"^Copyright\s+(\d{4})\s+(.+?)\s*$", self.text, re.M)
        self.assertIsNotNone(
            match,
            "NOTICE has no 'Copyright <year> <holder>' line; Apache-2.0 4(d) "
            "makes this line travel with every copy",
        )
        return match.group(2)

    def test_the_copyright_holder_is_named(self):
        holder = self.copyright_line()
        self.assertGreater(len(holder), 3, f"copyright holder {holder!r} is too short to be a name")
        lowered = holder.lower()
        for placeholder in self.PLACEHOLDERS:
            with self.subTest(placeholder=placeholder):
                self.assertNotIn(
                    placeholder,
                    lowered,
                    f"NOTICE names {holder!r} as the copyright holder, which is a "
                    "placeholder rather than a legal entity. See ADR-0011",
                )

    def test_the_licence_is_apache_2_0_consistently(self):
        """The contradiction ADR-0011 was written to end: manifests vs LICENSE."""
        import json

        self.assertIn("SPDX-License-Identifier: Apache-2.0", self.text)
        licence = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", licence)
        self.assertIn("Version 2.0, January 2004", licence)
        for gem in sorted((ROOT / "gems").iterdir()):
            manifest = gem / "gem.json"
            if not manifest.is_file():
                continue
            with self.subTest(gem=gem.name):
                self.assertEqual(
                    json.loads(manifest.read_text(encoding="utf-8")).get("license"),
                    "Apache-2.0",
                )

    def test_the_recorded_licence_hash_verifies(self):
        """NOTICE says to run `sha256sum LICENSE`. This runs it."""
        import hashlib

        match = re.search(r"committed \(LF\)\s+sha256\s+([0-9a-f]{64})", self.text)
        self.assertIsNotNone(
            match, "NOTICE records no sha256 for the committed LICENSE"
        )
        actual = hashlib.sha256((ROOT / "LICENSE").read_bytes()).hexdigest()
        self.assertEqual(
            actual,
            match.group(1),
            "the sha256 recorded in NOTICE does not match the committed LICENSE; "
            "a hash that cannot be checked against what is committed is worse "
            "than none, because it looks like verification (ADR-0011)",
        )

    def test_a_placeholder_would_be_caught(self):
        """Negative test: the check above must be able to fail.

        Without it, a regex that silently stopped matching would read exactly
        like a correctly named holder.
        """
        for bad in ("Copyright 2026 the Phoenix authors", "Copyright 2026 TODO"):
            with self.subTest(line=bad):
                holder = re.search(r"^Copyright\s+\d{4}\s+(.+?)\s*$", bad, re.M).group(1)
                self.assertTrue(
                    any(p in holder.lower() for p in self.PLACEHOLDERS),
                    f"{holder!r} should have been recognised as a placeholder",
                )
