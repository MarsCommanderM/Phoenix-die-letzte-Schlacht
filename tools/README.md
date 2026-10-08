# Tools

Tools are part of the product, not a convenience. The rule from
`docs/tdd/09-roadmap.md`: if a process has to be done manually and
repeatedly, automate it.

This directory follows the implementation rule in that chapter — a tool is
written when it can do real work. An empty placeholder is worse than an
absent file, because it looks like coverage.

## Present

| Tool | Does |
| --- | --- |
| `validation/validate_assets.py` | Asset authoring rules beyond schema validity: naming, id/filename agreement, cross-document references, orphan detection, schema coverage |
| `validation/validate_project.py` | Project and gem manifest contract, and agreement between `project.json` and the gems on disk |
| `migration/migrate_save.py` | Versioned save migration: runs a registered chain from any older schema version to current, and verifies the result |
| `profiling/analyze_budget.py` | Reads `project/Config/Performance/budgets.json` and reports which budgets can gate and which are still unset; compares a measurement file against the ones that can |

All four run without an engine, are covered by `tests/Unit/test_tools.py`,
and run in CI on every pull request. The save migration is tested for
determinism, purity (it does not mutate its input), refusal of a
newer-than-current save, and absence of gaps in the version chain.

## Deliberately absent — Class C

These are named in the source document but need something that does not exist
yet. Creating them now would produce files that cannot be run or tested.

| Tool | Blocked on |
| --- | --- |
| `assets/inspect_assets.py`, `assets/generate_asset_report.py` | processed product assets, which need the Asset Processor |
| `level/validate_level.py` | levels and prefabs; none authored yet |
| `networking/network_test_runner.py` | a dedicated server build and the test matrix harness |
| `migration/migrate_assets.py` | a second asset schema version to migrate between |
| `profiling/collect_metrics.py` | an instrumented build to collect from |

Each becomes Class A at the milestone that produces its input; see
`docs/tdd/09-roadmap.md`.
