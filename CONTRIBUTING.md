# Contributing

Changes must preserve the gem dependency direction, add tests for new runtime
behavior, and update an ADR for architectural changes.

## Before opening a pull request

```
python -m pip install -r requirements-dev.txt

python scripts/validate.py            # schemas, asset data, gem tiers
python scripts/check_architecture.py  # cycles, forbidden includes, owners
python scripts/check_cmake.py         # every CMake file list parses and resolves
python scripts/test.py                # repository contract tests

python tools/validation/validate_project.py        # project + gem manifests
python tools/validation/validate_assets.py         # asset authoring rules
python tools/validation/validate_asset_naming.py   # the naming convention
python tools/validation/validate_registries.py     # tags + collision layers
python tools/validation/validate_engine_patches.py # the engine patch register
python tools/validation/validate_versions.py       # the three version contracts
python tools/profiling/analyze_budget.py           # which budgets can gate

clang-format --dry-run -Werror $(find gems project -name '*.h' -o -name '*.cpp')
```

Every one of these runs in CI on every pull request
(`.github/workflows/pull_request.yml`), and
`tests/Unit/test_tools.py` fails if a tool exists that no workflow runs — a
validator that never executes passes forever and reads as coverage.

`clang-format` comes from `requirements-dev.txt` rather than your system
package manager, deliberately: different versions format the same file
differently, so an unpinned formatter makes CI disagree with the check you
just ran. `.clang-format` is the engine's own file, unmodified; see
[ADR-0012](docs/adr/0012-cpp-tooling.md) before changing it.

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

## Before creating a file

A file exists only if at least one of these is true. If none is, do not create
it — an empty placeholder is worse than an absent file, because it reads as
coverage.

- it owns behavior
- it owns data
- it defines a contract
- it is required by the build
- it is required at runtime
- it validates content
- it tests behavior
- it automates production
- it documents an architectural decision

## Changes that need elevated review

These carry consequences that outlive the pull request, so they need a second
reviewer and an explicit statement of the migration or rollback path:

| Change | Why |
| --- | --- |
| `project/project.json` | project identity and gem registration |
| any `CMakeLists.txt` or `*_files.cmake` | build graph |
| `project/Code/enabled_gems.cmake` | O3DE-managed; must change via `o3de enable-gem` |
| `project/Registry/*.setreg` | runtime configuration |
| `project/Config/save_schema.json` | save compatibility; needs a migration |
| `project/Config/network_protocol.json` | client/server compatibility |
| `project/Assets/Schema/*.schema.json` | authoring data contract |
| `LICENSE` / `NOTICE` | not retroactive; see [ADR-0011](docs/adr/0011-project-licence.md) |
| anything under `docs/engine-patches/` | engine fork liability; needs an ADR |

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
