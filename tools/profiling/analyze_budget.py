"""Report which Phoenix budgets can gate, and compare measurements against them.

docs/tdd/07-budgets.md states a budget without an automated check is treated
as absent. This tool makes that visible: it separates budgets that can fail a
build from budgets that are still unset, so "we have budgets" is never
confused with "our budgets are enforced".
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUDGETS = ROOT / "project" / "Config" / "Performance" / "budgets.json"

#: Keys that carry a threshold rather than metadata.
THRESHOLD_KEYS = (
    "targetMs",
    "warningMs",
    "criticalMs",
    "varianceCriticalMs",
    "targetBytes",
    "warningBytes",
    "hardLimitBytes",
    "rateHz",
    "maxVariantCount",
    "bytesPerSecondPerPlayer",
    "packetsPerSecond",
    "entitiesPerPlayer",
    "propertiesPerEntity",
    "replicationCpuMs",
)


def walk(node, path=()):
    """Yield (dotted path, key, value) for every threshold field."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key.startswith("$"):
                continue
            if key in THRESHOLD_KEYS:
                yield ".".join(path), key, value
            else:
                yield from walk(value, path + (key,))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--measurements",
        type=Path,
        help="JSON file of {dotted.path: {key: value}} measurements to compare",
    )
    parser.add_argument(
        "--require-all-set",
        action="store_true",
        help="exit non-zero if any budget is still unset; use at a gate that "
        "demands full budget coverage",
    )
    args = parser.parse_args()

    budgets = json.loads(BUDGETS.read_text(encoding="utf-8"))

    enforceable: dict[tuple[str, str], float] = {}
    unset: list[tuple[str, str]] = []
    for path, key, value in walk(budgets):
        if value is None:
            unset.append((path, key))
        else:
            enforceable[(path, key)] = value

    print(f"Budget coverage: {len(enforceable)} enforceable, {len(unset)} unset.")

    if unset:
        print("\nUnset — these cannot gate a build:")
        for path, key in unset:
            print(f"  {path or '(root)'}.{key}")

    if enforceable:
        print("\nEnforceable:")
        for (path, key), value in sorted(enforceable.items()):
            print(f"  {path or '(root)'}.{key} = {value}")

    exceeded = []
    if args.measurements:
        measured = json.loads(args.measurements.read_text(encoding="utf-8"))
        print("\nMeasurements:")
        for path, values in sorted(measured.items()):
            for key, actual in values.items():
                budget = enforceable.get((path, key))
                if budget is None:
                    print(f"  {path}.{key} = {actual} (no budget set; not gated)")
                    continue
                over = actual > budget
                verdict = "OVER" if over else "ok"
                print(f"  {path}.{key} = {actual} vs budget {budget} -> {verdict}")
                if over:
                    exceeded.append(f"{path}.{key}: {actual} > {budget}")

    if exceeded:
        print(f"\n{len(exceeded)} budget(s) exceeded:", file=sys.stderr)
        for item in exceeded:
            print(f"  - {item}", file=sys.stderr)
        raise SystemExit(1)

    if args.require_all_set and unset:
        print(
            f"\n{len(unset)} budget(s) still unset; this gate requires full coverage.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print("\nBudget analysis passed.")


if __name__ == "__main__":
    main()
