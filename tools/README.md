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
| `validation/validate_asset_naming.py` | The convention in `docs/production/naming.md`: production-asset prefixes, case collisions across the whole tree, forbidden path characters, forbidden `_final`/`_v2` suffixes, data-document prefixes |
| `validation/validate_project.py` | Project and gem manifest contract, and agreement between `project.json` and the gems on disk |
| `validation/validate_registries.py` | The two central registries: declared tag namespaces, and a collision matrix that is symmetric, complete and keeps index 0 reserved |
| `validation/validate_versions.py` | The three independently versioned contracts, their JSON Schemas, the compatibility window, the save migration chain, and agreement between `version.json` and `PhoenixVersion.h` |
| `validation/validate_engine_patches.py` | The engine patch register against the patch files on disk, in both directions, with every field ADR-0009 requires |
| `migration/migrate_save.py` | Versioned save migration: runs a registered chain from any older schema version to current, and verifies the result |
| `profiling/analyze_budget.py` | Reads `project/Config/Performance/budgets.json` and reports which budgets can gate and which are still unset; compares a measurement file against the ones that can |

All eight run without an engine and run in CI on every pull request. Each is
covered by tests under `tests/Unit/`, and every check that can reject
something has a negative test that proves it does: a validator nobody has
watched fail is a validator nobody knows works.

Two of them currently guard content that does not exist yet —
`validate_asset_naming.py` has no production assets to check and
`validate_engine_patches.py` has no patches — and both say so in their output
rather than printing a bare "passed". Their rules are exercised against
synthetic inputs in the test suite, so the first real asset and the first real
patch meet a gate that has already been shown to work.

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
