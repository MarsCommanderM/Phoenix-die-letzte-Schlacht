import subprocess
import sys
import unittest

import sys
from pathlib import Path

# Keep this module runnable on its own, not only via scripts/test.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from _repo import ROOT


def run_script(name):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / name)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class ValidationGateTests(unittest.TestCase):
    """The gates CI depends on must pass against the committed tree."""

    def test_validate_passes(self):
        result = run_script("validate.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cmake_check_passes(self):
        result = run_script("check_cmake.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
