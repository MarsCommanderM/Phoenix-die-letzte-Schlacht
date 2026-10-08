# 00 — Executive Summary

## Goal and management decision

Phoenix is developed as a high-fidelity first-person action game on a
controlled O3DE 26.05 fork using Atom/Vulkan, PhysX 5 and a server-authoritative
network architecture. The product launches on its single-player campaign;
public multiplayer follows a gate. The architecture prioritises stable frame
and server tick times, reproducible production, scalable content pipelines and
long-term maintainability.

Phoenix is not a new engine stack. It is a game system on O3DE: the engine
supplies infrastructure, Phoenix supplies only the difference between a generic
engine and the game actually required.

## The five core decisions

### 1. Controlled engine fork

O3DE is patched only for demonstrably engine-wide requirements. Gameplay and
project-specific functionality stay in Phoenix gems and project modules.

Every engine patch needs an ADR naming the upstream issue, why it cannot live
in a gem, and who owns rebasing it. The fork's patch set is a tracked
liability: the larger it grows, the more expensive every engine upgrade
becomes.

### 2. Server-authoritative multiplayer

Dedicated servers own all game-deciding, competitively relevant and persistent
state. Prediction is permitted only for explicitly approved state.

Phoenix builds on the O3DE Multiplayer Framework rather than beside it. The
framework already provides server authority, entity replication, RPCs, local
prediction and backwards reconciliation; Phoenix adds the FPS-specific
relevance, priority and gameplay layer on top. See
[04 — Multiplayer](04-multiplayer.md).

### 3. Modular, data-driven runtime

Rendering, gameplay, physics, animation, AI, audio, UI and world streaming
communicate through defined interfaces, events and versioned data assets.

The dependency direction is machine-checked, not merely documented: see
[02 — Architecture](02-architecture.md) and `scripts/validate.py`.

### 4. Central budgets and automated quality assurance

CPU, GPU, memory, network, shader, streaming and content are measurably
budgeted and enforced in CI, regression tests and release gates. A budget
without an automated check is treated as absent. See
[07 — Budgets](07-budgets.md) and [08 — Quality Gates](08-quality-gates.md).

### 5. Single-player launch anchor, multiplayer behind a gate

The launch anchor is the **single-player campaign**. The multiplayer
architecture — server authority, replication model, protocol versioning,
server validation — is built from the start, because authority cannot be
retrofitted into a shipped single-player codebase. Public multiplayer ships
only after the gate in [08](08-quality-gates.md).

Player count is a **measurement ladder, not a launch commitment**:
2 → 8 → 16 → 32, with 50 as a separate stretch gate. 50 players is a
measurement target; if it endangers product quality it moves post-launch
without architectural loss.

The architecture must support the campaign and a cell-based streaming world
without exceeding critical frame-time, tick-time or memory limits, and must
not foreclose the ladder above.

## The three largest risks

Summarised here; the full register with owners and triggers is
[10 — Risks](10-risks.md).

1. **Multiplayer and simulation scaling.** Players, AI, physics, streaming and
   replication can saturate server tick, CPU, bandwidth and memory
   simultaneously, and they do so together rather than one at a time.
   Countermeasure: climb the player ladder by measurement, interest
   management, replication budgets, server profiling and soak tests from the
   Foundation phase onward.
2. **Streaming and rendering stutter.** World streaming, shader variants, GPU
   uploads, temporal effects and volumetric systems can produce unpredictable
   frame-time spikes. Countermeasure: asynchronous cell-based streaming,
   deterministic shader builds, variant limits, fixed measurement scenes and
   automated performance regressions.
3. **Architecture and production complexity.** A growing engine fork, strong
   system coupling or uncontrolled feature scope can jeopardise upgrades,
   debugging, content production and release planning. Countermeasure:
   architecture reviews, acyclic gem dependencies, documented owners, feature
   gates, versioned data and a binding definition of done.

## Measurable acceptance criteria

Phoenix is technically acceptable when all five hold:

| # | Criterion | Verified by |
| --- | --- | --- |
| 1 | **Reproducible builds.** Client and dedicated-server builds reproduce from a defined commit with identical build metadata; all mandatory CI checks pass. | [08](08-quality-gates.md), `scripts/generate_manifest.py` |
| 2 | **Scaling.** Each rung of the player ladder reached so far passes the defined worst-case load test including AI, physics, replication and world streaming, without exceeding the central CPU, network, memory and server-tick budgets. A rung is not claimed until measured. | [07](07-budgets.md), load test suite |
| 3 | **Frame-time stability.** The defined streaming, shader and render regression tests show no critical frame-time spikes or uncontrolled memory peaks; any deviation is detected automatically and assigned to an owner. | [05](05-rendering.md), [08](08-quality-gates.md) |
| 4 | **Network reliability.** Prediction, reconciliation, interest management and server validation work across the full network test matrix including high latency, jitter, packet loss and reordering. | [04](04-multiplayer.md) |
| 5 | **Persistence and operations.** Save schemas, asset schemas, network protocols and backend contracts are versioned and migratable; 24-hour server soak tests, crash reporting, telemetry, security review, accessibility tests and all release gates pass. | [06](06-data-schemas.md), [08](08-quality-gates.md) |

**Management conclusion.** The technical architecture is approvable provided
scaling, streaming stability and architectural discipline are demonstrated
early through measurable gates. Without those demonstrations, neither full
production nor content scaling may begin.

## What changed against the original draft

Three corrections define the technical level of this document. They are
recorded because each one removes a substantial amount of planned work.

| Original intent | Decision | Reason |
| --- | --- | --- |
| Build a largely custom renderer inside O3DE | Use Atom and extend it through RPI render passes | Atom is already designed as a modular renderer and RPI exists precisely to add custom passes and features. Phoenix cinematic technology belongs there. |
| Build a parallel network stack beside the O3DE Multiplayer Framework | Build on the framework, add the FPS relevance/priority/gameplay layer above it | The framework already supplies server authority, entity replication, RPCs, local prediction and backwards reconciliation. Re-implementing those is cost without differentiation. |
| One AZSL shader performing fog + blur + ACES + grain + letterbox | Decompose into composable Atom render passes | Atom treats these as separate, reorderable passes; AZSL and shader assets are then processed by the existing shader build pipeline. A monolithic shader cannot be reordered, budgeted or disabled per platform. |

Six further contradictions between the three source documents are resolved in
[90 — Source Reconciliation](90-source-reconciliation.md), including the launch
anchor and player scale above. Where this document and a source document
disagree, that chapter records which won and why.

The next engineering step is not more theory but the concrete implementation
specification: `project.json`, the real gem CMake structure, target and library
dependencies, concrete C++ interfaces, multiplayer component schemas, data
asset schemas, the Atom pass hierarchy, build presets, and the exact order of
the first 12–16 weeks. Chapters 01–09 are that specification.
