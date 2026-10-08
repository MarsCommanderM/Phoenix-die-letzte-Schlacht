"""The C++ tooling contract: .clang-format and .clang-tidy.

Two files that are easy to ship and easy to have lie to you. A .clang-format
the tree already violates is not a style, it is a pending 60-file diff that
the next person will be blamed for. A .clang-tidy naming a check that clang
does not have is silently ignored, so the gate reads as enabled and enforces
nothing.

These tests check both against the installed tools rather than against a
transcription of what the files are supposed to say, and each positive check
is paired with a negative one, so a gate that stopped working fails here
instead of passing quietly.
"""
import hashlib
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT  # noqa: E402

CLANG_FORMAT = ROOT / ".clang-format"
CLANG_TIDY = ROOT / ".clang-tidy"

#: sha256 of the .clang-format blob at O3DE tag 2605.0, recorded so that an
#: edit to the committed file has to be a deliberate, reviewed divergence from
#: the engine's published style rather than a drift nobody noticed. See
#: docs/adr/0012-cpp-tooling.md.
UPSTREAM_CLANG_FORMAT_SHA256 = (
    "4857426bd80a3d4ff6847d05e597f193c0cad839a7890de4f32782f6ff9795ab"
)


def cpp_sources() -> list[Path]:
    """Every Phoenix C++ translation unit and header."""
    out: list[Path] = []
    for base in (ROOT / "gems", ROOT / "project"):
        out += sorted(base.rglob("*.h")) + sorted(base.rglob("*.cpp"))
    return sorted(out)


def named_checks(text: str) -> list[str]:
    """The check names inside the `Checks: >` block of a .clang-tidy document.

    Parsed rather than imported because clang-tidy offers no way to print the
    literal list back; `--list-checks` prints the resolved set, which is what
    the comparison below is for.
    """
    match = re.search(r"^Checks:\s*>\s*\n((?:[ \t]+\S.*\n)+)", text, re.M)
    if match is None:
        return []
    return [
        item
        for item in (part.strip().rstrip(",") for part in match.group(1).split(","))
        if item and item != "-*"
    ]


class ClangFormatTests(unittest.TestCase):
    def setUp(self):
        self.clang_format = shutil.which("clang-format")

    def test_config_exists_and_matches_the_engine(self):
        """The style is the engine's, byte for byte, not an invented one.

        Phoenix is built on O3DE and read by people with O3DE habits. A hash
        that cannot be checked against what is committed would be worse than
        none, so this compares the committed file itself.
        """
        self.assertTrue(CLANG_FORMAT.is_file(), ".clang-format is missing")
        digest = hashlib.sha256(CLANG_FORMAT.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            UPSTREAM_CLANG_FORMAT_SHA256,
            ".clang-format no longer matches O3DE 2605.0. Diverging is allowed, "
            "but it is an ADR-0012 decision: update the ADR and this hash in the "
            "same change, so the divergence is visible.",
        )

    def test_the_tree_already_conforms(self):
        """Running clang-format over the repository must change nothing."""
        if self.clang_format is None:
            self.skipTest("clang-format is not installed")
        sources = cpp_sources()
        self.assertGreater(len(sources), 0, "no C++ sources found to check")
        result = subprocess.run(
            [self.clang_format, "--dry-run", "-Werror", *map(str, sources)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            "clang-format would rewrite committed sources:\n" + result.stderr[:4000],
        )

    def test_the_check_rejects_misformatted_code(self):
        """Negative test: prove the check above can fail at all.

        Without this, a --dry-run that silently stopped inspecting files would
        read exactly like a clean tree.
        """
        if self.clang_format is None:
            self.skipTest("clang-format is not installed")
        # Written inside the repository tree so the committed .clang-format is
        # the one that applies; build/ is excluded from every other gate.
        bad = ROOT / "build" / "clang_format_negative_check.cpp"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text(
            "namespace Phoenix{ class Bad{int  x ;};}\n",
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                [self.clang_format, "--dry-run", "-Werror", str(bad)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        finally:
            bad.unlink(missing_ok=True)
        self.assertNotEqual(
            result.returncode, 0, "clang-format accepted deliberately broken code"
        )


class ClangTidyTests(unittest.TestCase):
    def setUp(self):
        self.clang_tidy = shutil.which("clang-tidy")
        self.text = CLANG_TIDY.read_text(encoding="utf-8") if CLANG_TIDY.is_file() else ""

    def test_config_exists(self):
        self.assertTrue(CLANG_TIDY.is_file(), ".clang-tidy is missing")

    def test_the_check_list_is_explicit(self):
        """No wildcards. Each check is listed, so each one was a decision."""
        checks = named_checks(self.text)
        self.assertGreater(len(checks), 20, "the check list did not parse")
        for check in checks:
            with self.subTest(check=check):
                self.assertNotIn(
                    "*", check, f"'{check}' is a wildcard; enable checks one by one"
                )

    def test_every_named_check_is_one_clang_tidy_knows(self):
        """A misspelled check is not an error to clang-tidy — it is a no-op.

        That is the failure this test exists for: the file would look like a
        67-check gate while enforcing 66, or none.
        """
        if self.clang_tidy is None:
            self.skipTest("clang-tidy is not installed")
        named = named_checks(self.text)
        self.assertTrue(named)
        result = subprocess.run(
            [self.clang_tidy, f"--config-file={CLANG_TIDY}", "--list-checks"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr[:2000])
        resolved = {
            line.strip() for line in result.stdout.splitlines() if line.startswith("    ")
        }
        self.assertEqual(
            sorted(resolved),
            sorted(named),
            "the checks clang-tidy resolved differ from the checks named in "
            ".clang-tidy; a name on the left that is missing on the right is a "
            "typo that silently disables itself",
        )

    def test_warnings_are_errors(self):
        """A warning nobody must fix is a warning nobody fixes."""
        self.assertRegex(self.text, re.compile(r"^WarningsAsErrors:\s*'\*'\s*$", re.M))

    def test_header_filter_is_scoped_to_phoenix_code(self):
        """Engine and third-party headers are not ours to fix."""
        match = re.search(r"^HeaderFilterRegex:\s*'(.+)'\s*$", self.text, re.M)
        self.assertIsNotNone(match, "HeaderFilterRegex is not set")
        pattern = re.compile(match.group(1))
        self.assertTrue(
            pattern.search("gems/PhoenixCore/Code/Include/Phoenix/Core/PhoenixIds.h"),
            "the filter excludes Phoenix's own headers",
        )
        self.assertFalse(
            pattern.search("/opt/o3de/Code/Framework/AzCore/AzCore/Component/Component.h"),
            "the filter admits engine headers",
        )

    def test_it_states_why_it_is_not_a_ci_gate_yet(self):
        """clang-tidy needs a compilation database, which needs the engine.

        Recording that in the file is the difference between a declaration and
        a claim of coverage this repository cannot back.
        """
        self.assertIn("compile_commands.json", self.text)


if __name__ == "__main__":
    unittest.main()
