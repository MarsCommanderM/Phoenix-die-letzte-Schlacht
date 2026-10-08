# Phoenix — die letzte Schlacht

High-fidelity first-person action game on Open 3D Engine 26.05.0.

**Start here: [Technical Design Document v1.0](docs/tdd/README.md).** It is the
shared technical reference for Engineering, Gameplay, Art, Audio, QA, Online
and Production.

## Baseline

| Area | Choice |
| --- | --- |
| Engine | O3DE 26.05.0, pinned exactly |
| Renderer | Atom / RPI / RHI, Vulkan |
| Physics | PhysX 5 |
| Animation | EMotionFX |
| Multiplayer | O3DE Multiplayer / AzNetworking |
| UI | LyShine |
| Build | O3DE CMake / O3DE CLI |
| Targets | Windows client, Linux dedicated server |

The launch anchor is the **single-player campaign**; public multiplayer follows
a gate. See [ADR-0007](docs/adr/0007-launch-anchor-and-player-scale.md).

Phoenix is not a new engine stack. The engine supplies infrastructure; Phoenix
supplies only the difference between a generic engine and the game actually
required. No custom ECS, renderer, physics, animation runtime, network
protocol, asset pipeline, UI framework or build system.

## Engine setup

`engine/o3de/` is intentionally not committed. Register a local O3DE 26.05.0
engine; `project/cmake/EngineFinder.cmake` is produced by that registration and
is machine-local.

1. Register the Phoenix project with O3DE.
2. Register the external Phoenix gems if needed.
3. Enable the required gems with `o3de enable-gem` — never hand-edit
   `project/Code/enabled_gems.cmake`.
4. Configure and build via the presets in `CMakePresets.json`, or the O3DE CLI.

## Static validation — no engine required

```
python -m pip install -r requirements-dev.txt
python scripts/validate.py      # schemas, asset data, gem tiers, CMake/manifest agreement
python scripts/check_cmake.py   # every CMake list parses and every declared path resolves
python scripts/test.py          # repository contract, structure and documentation tests
```

All three run on every pull request. `scripts/test.py` fails on an empty
suite, so the gate cannot pass without executing anything.

## Layout

| Path | Contents |
| --- | --- |
| `docs/tdd/` | Technical Design Document v1.0 |
| `docs/adr/` | Architecture decision records, registered in [docs/adr/README.md](docs/adr/README.md) |
| `docs/implementation/` | Interface contracts, multiplayer component schemas, verified boundaries |
| `gems/` | Eight Phoenix domain gems; tiers in [TDD 02](docs/tdd/02-architecture.md) |
| `project/` | O3DE project: manifest, code, assets, config, registry |
| `scripts/` | Configure, build, validate, test, package, release helpers |
| `tests/` | Repository contract, structure and documentation tests |
| `.github/workflows/` | CI |

## Open items

[`docs/implementation/verified-boundaries.md`](docs/implementation/verified-boundaries.md)
lists values that could not be verified without a registered engine, and
decisions deliberately left to their owners — including the licence mismatch
between `LICENSE` and the gem manifests. Resolving them is Week 1 of
[TDD 09](docs/tdd/09-roadmap.md).
