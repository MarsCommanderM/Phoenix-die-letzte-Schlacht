# Phoenix — O3DE 26.05.0 Starter Repository

This repository is the implementation baseline for the Phoenix technical design.

## Baseline
- O3DE: 26.05.0
- Renderer: Atom / RPI / RHI
- Physics: PhysX
- Animation: EMotionFX
- Multiplayer: O3DE Multiplayer / AzNetworking
- Build: O3DE CMake / CLI
- Primary target: Windows

## Important
The `engine/o3de/` directory is intentionally not included. Register your
local O3DE 26.05.0 engine separately.

`project/Code/enabled_gems.cmake` is O3DE-managed. Use the O3DE CLI to
enable/disable Gems.

## Configure
1. Register the Phoenix project with O3DE.
2. Register the external Phoenix Gems if needed.
3. Enable the required O3DE Gems.
4. Configure and build using O3DE CLI / Project Manager.

The source tree is intentionally conservative: generated AutoComponent C++
and processed asset products are not committed.

## Static validation

The repository validates without an engine installed:

```
python -m pip install -r requirements-dev.txt
python scripts/validate.py      # schemas, asset data, gem dependency tiers
python scripts/check_cmake.py   # every CMake file list parses and resolves
python scripts/test.py          # repository contract tests
```

## Layout

| Path | Contents |
| --- | --- |
| `gems/` | Eight Phoenix domain gems; see `docs/architecture/README.md` for the tiers |
| `project/` | O3DE project: manifest, code, assets, config, registry |
| `scripts/` | Configure/build/validate/package helpers |
| `tests/` | Repository contract tests |
| `docs/adr/` | Architecture decision records, indexed in `docs/adr/README.md` |
| `.github/workflows/` | CI |

## Known unresolved items

`docs/implementation/verified-boundaries.md` lists values inherited from the
initial starter that could not be verified without a registered O3DE
26.05.0 engine — the engine gem names, the settings registry root, and the
licence mismatch between `LICENSE` and the gem manifests. Resolve these
before distribution.
