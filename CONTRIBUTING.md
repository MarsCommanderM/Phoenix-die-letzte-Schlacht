# Contributing

Changes must preserve the gem dependency direction, add tests for new runtime
behavior, and update an ADR for architectural changes.

## Before opening a pull request

```
python -m pip install -r requirements-dev.txt
python scripts/validate.py      # schemas, asset data, gem tiers
python scripts/check_cmake.py   # every CMake file list parses and resolves
python scripts/test.py          # repository contract tests
```

All three run in CI on every pull request (`.github/workflows/pull_request.yml`).

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
- `gems/*/CMakeLists.txt` and `project/Code/Phoenix_files.cmake` list files
  that exist on disk; `scripts/check_cmake.py` fails if they drift.
