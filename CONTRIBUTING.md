# Contributing

Changes must preserve the gem dependency direction, add tests for new runtime
behavior, and update an ADR for architectural changes.

## Before opening a pull request

```
python -m pip install -r requirements-dev.txt
python scripts/validate.py      # schemas, asset data, gem tiers
python scripts/check_cmake.py   # every CMake file list parses and resolves
python scripts/test.py          # repository contract tests

python tools/validation/validate_project.py   # project + gem manifests
python tools/validation/validate_assets.py    # asset authoring rules
python tools/profiling/analyze_budget.py      # which budgets can gate
```

All three run in CI on every pull request (`.github/workflows/pull_request.yml`).

## Architecture review

Every pull request answers the nine questions in
[TDD 08](docs/tdd/08-quality-gates.md): which layer changes, which dependency
is added, is it necessary, does O3DE already provide it, is the new API
Phoenix-owned, is persistence affected, is networking affected, is performance
affected, which tests were added.

## Dependency direction

`docs/architecture/README.md` defines four gem tiers and
`scripts/validate.py` enforces them. A dependency that does not point
strictly downward fails validation. Adding a gem means updating `TIERS` in
`scripts/validate.py` and `EXPECTED_GEMS` in
`tests/Unit/test_repository_contract.py`.

## Generated files

- `project/Code/enabled_gems.cmake` is O3DE-managed; change it with
  `o3de enable-gem` / `o3de disable-gem`, not by hand.
- AutoComponent C++ is generated from `*.AutoComponent.xml` by O3DE
  Multiplayer and is not committed.
- Manual sources, generated inputs and gem activation are three separate
  responsibilities in three separate places: `*_{api,private,shared}_files.cmake`,
  `Phoenix_autogen_files.cmake`, `enabled_gems.cmake`. Never merge them.
- Every CMake list declares files that exist on disk; `scripts/check_cmake.py`
  fails if they drift, and `scripts/validate.py` fails if a gem's CMake
  `BUILD_DEPENDENCIES` stop matching its `gem.json`.
