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
