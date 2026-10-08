"""The build manifest: reproducible identity, and no invented facts.

scripts/generate_manifest.py answers one question — "are these two artefacts
the same build?" — and there are exactly two ways for it to answer wrongly.

A nondeterministic buildId makes two builds of the same commit look
different, which is the question inverted. A clock or a random value sneaking
into the id is enough, and nothing about the output would look wrong, so the
determinism tests here are the only thing standing between the id and that.

A fabricated identity field makes two unlike artefacts look the same. The
machine generating a manifest need not be the machine that performed the
build, so every field the script cannot actually read must come out null and
warned about rather than guessed from the local environment. These tests
check that each null is admitted.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_manifest as manifest  # noqa: E402

TOOLCHAIN = {
    "compiler": "clang-18.1.3",
    "sdk": "linux-glibc-2.39",
    "platform": "linux_x64",
    "configuration": "profile",
}
EMPTY_TOOLCHAIN = {field: None for field in manifest.TOOLCHAIN_FIELDS}


def tiny_tree(directory: Path, *, engines=("o3de==26.05.0",), requirements="jsonschema==4.26.0\n"):
    """A minimal tree with the four things the readers look at."""
    (directory / "project").mkdir(parents=True, exist_ok=True)
    (directory / "project" / "project.json").write_text(
        json.dumps({"project_name": "Phoenix", "compatible_engines": list(engines)}),
        encoding="utf-8",
    )
    config = directory / "project" / "Config"
    config.mkdir(parents=True, exist_ok=True)
    for name, document in (
        ("version.json", {"product": "Phoenix", "major": 0, "minor": 1, "patch": 0}),
        ("network_protocol.json", {"protocol": 1, "minimumCompatible": 1, "maximumCompatible": 1}),
        ("save_schema.json", {"current": 2, "minimumReadable": 1}),
    ):
        (config / name).write_text(json.dumps(document), encoding="utf-8")
    gem = directory / "gems" / "PhoenixCore"
    gem.mkdir(parents=True, exist_ok=True)
    (gem / "gem.json").write_text(
        json.dumps({"gem_name": "PhoenixCore", "version": "0.1.0"}), encoding="utf-8"
    )
    (directory / "requirements-dev.txt").write_text(requirements, encoding="utf-8")
    return directory


class BuildIdTests(unittest.TestCase):
    def test_it_is_deterministic_across_runs(self):
        """Same tree, same identity, same id. The whole point of the field."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            first = manifest.build_manifest(root, dict(TOOLCHAIN))
            second = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertEqual(first["build"]["buildId"], second["build"]["buildId"])

    def test_the_id_is_the_hash_of_the_recorded_content(self):
        """Recomputed from what was written, so a clock cannot hide in it."""
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
        recomputed = manifest.compute_build_id(document["files"], document["build"])
        self.assertEqual(document["build"]["buildId"], recomputed)

    def test_the_source_imports_no_clock_or_randomness(self):
        """A timestamped id would defeat the only question the id answers."""
        source = (ROOT / "scripts" / "generate_manifest.py").read_text(encoding="utf-8")
        for forbidden in ("import time", "import random", "import datetime", "from datetime"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_a_changed_identity_field_changes_the_id(self):
        """Otherwise a client and a server build of one commit share an id."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            base = manifest.build_manifest(root, dict(TOOLCHAIN))
            for field in manifest.TOOLCHAIN_FIELDS:
                toolchain = dict(TOOLCHAIN)
                toolchain[field] = "something-else"
                with self.subTest(field=field):
                    other = manifest.build_manifest(root, toolchain)
                    self.assertNotEqual(
                        base["build"]["buildId"],
                        other["build"]["buildId"],
                        f"changing {field} did not change the buildId",
                    )

    def test_a_changed_file_changes_the_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            base = manifest.build_manifest(root, dict(TOOLCHAIN))
            (root / "requirements-dev.txt").write_text(
                "jsonschema==4.26.1\n", encoding="utf-8"
            )
            other = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertNotEqual(base["build"]["buildId"], other["build"]["buildId"])

    def test_warnings_do_not_enter_the_id(self):
        """They only restate nulls that are already inside the identity block."""
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
        build = copy.deepcopy(document["build"])
        self.assertEqual(
            manifest.compute_build_id(document["files"], build),
            manifest.compute_build_id(document["files"], build),
        )
        # The payload is built from "build" and "files" only; prove warnings are
        # not reachable from it by changing them and recomputing.
        document["warnings"].append("a new warning")
        self.assertEqual(
            document["build"]["buildId"],
            manifest.compute_build_id(document["files"], document["build"]),
        )


class NullsAreAdmittedTests(unittest.TestCase):
    def test_every_unset_toolchain_field_is_null_and_warned(self):
        """A plausible-looking wrong value is believed and never questioned."""
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(EMPTY_TOOLCHAIN))
        for field in manifest.TOOLCHAIN_FIELDS:
            with self.subTest(field=field):
                self.assertIsNone(document["build"][field])
                self.assertTrue(
                    any(error.startswith(f"{field} is null") for error in document["warnings"]),
                    f"{field} is null with no warning: {document['warnings']}",
                )

    def test_the_engine_commit_is_always_null_and_always_warned(self):
        """The engine is not vendored here, so only the build agent knows it."""
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
        self.assertIsNone(document["build"]["engineCommit"])
        self.assertTrue(
            any("engineCommit is null" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_several_engine_pins_produce_null_rather_than_a_guess(self):
        """Picking the first would be a guess dressed up as a fact."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp), engines=("o3de==26.05.0", "o3de==26.10.0"))
            document = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertIsNone(document["build"]["engineVersion"])
        self.assertTrue(
            any("does not pin exactly one" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_one_engine_pin_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
        self.assertEqual(document["build"]["engineVersion"], "26.05.0")

    def test_an_unpinned_requirement_is_not_recorded(self):
        """It resolves differently on different days, so it is not an identity."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp), requirements="jsonschema\npytest==8.0.0\n")
            document = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertEqual(document["build"]["thirdPartyVersions"], {"pytest": "8.0.0"})
        self.assertTrue(
            any("is not an == pin" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_a_missing_contract_file_is_null_and_warned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            (root / "project" / "Config" / "save_schema.json").unlink()
            document = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertIsNone(document["build"]["saveSchema"])
        self.assertTrue(
            any("saveSchema is null" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_a_gem_without_a_version_is_null_and_warned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            (root / "gems" / "PhoenixCore" / "gem.json").write_text(
                json.dumps({"gem_name": "PhoenixCore"}), encoding="utf-8"
            )
            document = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertIsNone(document["build"]["gemVersions"]["PhoenixCore"])
        self.assertTrue(
            any("gemVersions['PhoenixCore'] is null" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_contract_comment_keys_are_excluded(self):
        """Rewording a $comment must not change the buildId; a bump must."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            path = root / "project" / "Config" / "save_schema.json"
            base = manifest.build_manifest(root, dict(TOOLCHAIN))
            path.write_text(
                json.dumps({"$comment": "reworded", "current": 2, "minimumReadable": 1}),
                encoding="utf-8",
            )
            reworded = manifest.build_manifest(root, dict(TOOLCHAIN))
            path.write_text(
                json.dumps({"current": 3, "minimumReadable": 1}), encoding="utf-8"
            )
            bumped = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertEqual(base["build"]["saveSchema"], reworded["build"]["saveSchema"])
        self.assertNotEqual(base["build"]["saveSchema"], bumped["build"]["saveSchema"])


class DirtyTreeTests(unittest.TestCase):
    def test_a_tree_with_no_git_metadata_is_null_and_warned(self):
        """An exported tarball has no git data; that is a fact, not a crash."""
        with tempfile.TemporaryDirectory() as tmp:
            # GIT_CEILING_DIRECTORIES stops git walking up into a real repo.
            os.environ["GIT_CEILING_DIRECTORIES"] = tmp
            try:
                document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
            finally:
                os.environ.pop("GIT_CEILING_DIRECTORIES", None)
        self.assertIsNone(document["build"]["projectCommit"])
        self.assertTrue(
            any("projectCommit is null" in w for w in document["warnings"]),
            document["warnings"],
        )

    def test_a_dirty_tree_says_so(self):
        """A commit recorded from a dirty tree names a build it cannot reproduce."""
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                   "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
            for args in (
                ["init", "-q"],
                ["add", "-A"],
                ["commit", "-qm", "seed"],
            ):
                subprocess.run(["git", *args], cwd=root, env=env, check=True,
                               capture_output=True)
            clean = manifest.build_manifest(root, dict(TOOLCHAIN))
            self.assertIsNotNone(clean["build"]["projectCommit"])
            self.assertFalse(clean["build"]["projectTreeDirty"])

            (root / "requirements-dev.txt").write_text("jsonschema==9.9.9\n", encoding="utf-8")
            dirty = manifest.build_manifest(root, dict(TOOLCHAIN))
        self.assertTrue(dirty["build"]["projectTreeDirty"])
        self.assertTrue(
            any("does not identify a reproducible build" in w for w in dirty["warnings"]),
            dirty["warnings"],
        )


class ConsumerShapeTests(unittest.TestCase):
    """release.yml publishes this file; its existing readers must keep working."""

    def test_the_original_fields_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = manifest.build_manifest(tiny_tree(Path(tmp)), dict(TOOLCHAIN))
        self.assertEqual(document["project"], "Phoenix")
        self.assertIsInstance(document["files"], list)
        for entry in document["files"]:
            self.assertEqual(sorted(entry), ["path", "sha256", "size"])

    def test_recorded_hashes_are_the_files_real_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = tiny_tree(Path(tmp))
            document = manifest.build_manifest(root, dict(TOOLCHAIN))
            for entry in document["files"]:
                path = root / entry["path"]
                with self.subTest(path=entry["path"]):
                    self.assertEqual(
                        hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"]
                    )
                    self.assertEqual(path.stat().st_size, entry["size"])

    def test_the_default_output_lies_outside_the_hashed_tree(self):
        """A manifest that hashes itself has no stable buildId."""
        self.assertEqual(manifest.DEFAULT_OUTPUT.parent.name, "build")
        from _repo import is_excluded

        self.assertTrue(is_excluded(manifest.DEFAULT_OUTPUT))


class RealRepositoryTests(unittest.TestCase):
    def test_it_runs_against_the_committed_tree(self):
        document = manifest.build_manifest(ROOT, dict(TOOLCHAIN))
        self.assertGreater(len(document["files"]), 100)
        self.assertEqual(document["build"]["engineVersion"], "26.05.0")
        self.assertEqual(len(document["build"]["gemVersions"]), 8)
        self.assertEqual(len(document["build"]["buildId"]), 64)

    def test_the_cli_writes_a_file_and_reports_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "manifest.json"
            result = subprocess.run(
                [sys.executable, "-I", str(ROOT / "scripts" / "generate_manifest.py"),
                 "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr[:2000])
            self.assertTrue(output.is_file())
            document = json.loads(output.read_text(encoding="utf-8"))
        self.assertIn("buildId", document["build"])
        self.assertIn("engineCommit is null", result.stderr)


if __name__ == "__main__":
    unittest.main()
