"""Run the Phoenix repository test suite.

The imported starter discovered from tests/ while tests/Unit/ was not a
package, so unittest recursed into nothing: the suite reported "Ran 0 tests"
and exited 0, making the CI test step pass without executing anything. This
sets an explicit top-level directory and fails when no test is collected.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Test modules import the shared repository helpers from scripts/.
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> None:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(ROOT / "tests"),
        pattern="test_*.py",
        top_level_dir=str(ROOT),
    )

    collected = suite.countTestCases()
    if collected == 0:
        print(
            "ERROR: no tests were collected. Discovery is broken -- a green "
            "run here would be meaningless.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(f"Collected {collected} tests.")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
