# 01 — Engine Baseline and Fork Policy

## Pinned baseline

| Area | Choice |
| --- | --- |
| Engine | O3DE 26.05.0, pinned exactly (`compatible_engines: ["o3de==26.05.0"]`) |
| Renderer | Atom, via RPI (Render Pipeline Interface) and RHI |
| Graphics API | Vulkan as the primary target |
| Physics | PhysX 5 — the default for new O3DE 26.05 projects. Gem name: **`PhysX5`**, not `PhysX` |
| Animation | EMotionFX |
| Shaders | AZSL, compiled to platform shaders by the asset pipeline |
| Multiplayer | O3DE Multiplayer Framework over AzNetworking |
| Build | O3DE CMake / CLI |
| Primary platform | Windows (client), Linux (dedicated server) |

The engine itself is not vendored into this repository. `engine/o3de/` is
intentionally absent; each developer and build agent registers a local
O3DE 26.05.0 engine. `project/cmake/EngineFinder.cmake` is written by that
registration and is machine-local, so it is not committed.

## Why these are pinned exactly

An exact engine pin is what makes acceptance criterion 1 (reproducible builds)
achievable. A range such as `>=26.05` would let two agents produce different
binaries from one commit, which breaks every downstream performance
comparison: a frame-time regression could no longer be attributed to a Phoenix
change rather than an engine change.

## Fork policy

O3DE is forked under control. The rules:

1. A patch to the engine requires an ADR naming the upstream issue, why the
   change cannot live in a Phoenix gem, and the engineer who owns rebasing it.
2. Anything achievable through a gem, an RPI pass, a component, or a data
   asset is **not** an engine patch. This covers almost all Phoenix-specific
   rendering, gameplay and networking work.
3. The patch set is reviewed at every engine upgrade. A patch whose upstream
   issue has been fixed is dropped rather than carried.
4. The fork never diverges in file formats, asset schemas or serialisation
   identity without an ADR, because those changes are not reversible once
   content exists.

Rationale: the cost of a fork is not the initial patch, it is every subsequent
upgrade multiplied by the patch count. Treating the patch set as a tracked
liability keeps that cost visible rather than discovering it at upgrade time.

## What the engine already provides

Recorded explicitly, because the original draft planned to rebuild several of
these. Building beside them would be cost without differentiation.

**Atom / RPI.** Atom is a modular, pass-driven and data-driven renderer. RPI
exists to let a project add its own render passes and features. Phoenix
cinematic technology is therefore implemented as RPI passes, not as a parallel
renderer. See [05 — Rendering](05-rendering.md).

**AZSL and the shader pipeline.** Shader source is authored in AZSL and
compiled to platform shaders by the asset pipeline, including variant
handling. Phoenix does not hand-manage platform shader binaries; it manages
variant *count*, which is a budget. See [07 — Budgets](07-budgets.md).

**PhysX 5.** Collision, rigid bodies, character controllers and scene queries
come from PhysX 5. Phoenix owns gameplay rules and query abstractions only;
it does not own the solver. See ADR-0003.

**Multiplayer Framework.** Server authority, entity replication, RPCs, local
prediction and backwards reconciliation are provided. Phoenix adds relevance,
priority and the FPS gameplay layer. See [04 — Multiplayer](04-multiplayer.md).

**SaveData.** Engine and platform persistence integration is provided. Phoenix
owns the save *schema* and its migrations. See ADR-0004 and
[06 — Data Schemas](06-data-schemas.md).

## Engine gem scope

Phoenix enables only the engine gems it actually needs. Each enabled gem adds
build time, descriptor registration, asset-processing work and QA surface, so
the enabled set is a scope decision rather than a convenience.

Declared as dependencies (all verified to exist at `2605.0`):

`Atom`, `PhysX5`, `EMotionFX`, `Multiplayer`, `AudioSystem`, `LyShine`,
`RecastNavigation`, `SaveData`.

**Deliberately not enabled by default.** These are useful and may be enabled
later against a concrete need, but none is a blanket requirement:

`ScriptCanvas`, `ScriptEvents`, `GradientSignal`, `FastNoise`,
`MultiplayerCompression`, `PythonAssetBuilder`, `AssetValidation`.

`SceneProcessing` is enabled at the **project** level with `o3de enable-gem`
rather than declared as a gem dependency: it is asset-processing
infrastructure, not a runtime dependency of any gameplay gem.

Adding an engine gem needs a stated need, the same as adding a third-party
dependency.

## Verification status

The engine dependencies and the gem build structure **have** been verified
against the engine source at tag `2605.0`. Three dependency names were wrong
and are corrected; see
[ADR-0010](../adr/0010-engine-dependency-verification.md) and
`docs/implementation/verified-boundaries.md`.

The one worth knowing here: the gem registered as `PhysX` is the **PhysX 4**
gem. This baseline pins PhysX 5, whose gem is `PhysX5`. Declaring `PhysX`
would have activated PhysX 4 successfully and silently, with nothing to report
the mismatch.

| Area | Status |
| --- | --- |
| Engine gem names | verified; `PhysX`→`PhysX5`, `Navigation`→`RecastNavigation`, `Prefab` dropped |
| Gem build structure | verified against `Gems/RecastNavigation`: three targets, `o3de_gem_setup`, five-argument `o3de_pal_dir` |
| File-list naming | verified; `<gemlower>_{api,private,shared}_files.cmake` matches the engine |
| Settings registry root | both `Amazon` and `O3DE` are in active engine use; the project's own root is **OPEN** |
| AutoComponent attributes | **not** verified; needs a registered engine to run the generator |
| `LICENSE` vs gem manifests | **resolved**: Apache-2.0, see [ADR-0011](../adr/0011-project-licence.md) |

Remaining open items are tracked in
`docs/implementation/verified-boundaries.md`. Closing them is Week 1 of
[09 — Roadmap](09-roadmap.md).
