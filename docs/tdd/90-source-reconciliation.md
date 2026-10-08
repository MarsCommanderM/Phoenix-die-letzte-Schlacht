# 90 — Source Reconciliation

This TDD consolidates three source documents that were supplied as the
project brief:

| Source | Title |
| --- | --- |
| **S1** | Master Technical Design & Production Document, v5.2 "Implementation-Complete Master Baseline" |
| **S2** | MVP section 6A, "Prioritisiertes MVP-Backlog" |
| **S3** | Master Technical Design & Production Specification, Revision 4.0 "Architecture Baseline" |

Four earlier revisions were supplied afterwards and identified as superseded:
AAA FPS TDD v1.0, Production Bible v3.0, Production Bible v3.2, and a
standalone Executive Summary. They do not override S1–S3, but three of them
decided things S1–S3 left open, and one corrected an error of mine. Those
contributions are recorded in **C7–C10** below.

They overlap heavily and **contradict each other in six places**. A
specification that contradicts itself cannot be implemented against, so each
conflict is resolved here, once, with the reason. Where this document and a
source disagree, **this document wins** and the entry below says why.

## C1 — Launch anchor and player scale

| Source | Position |
| --- | --- |
| S1 §101 | "50+ Player Production" is explicitly **not** MVP |
| S2 §6A.26 | Ladder 1→2→4→8→16→32; "50 Spieler bleiben ein separates Stretch-Gate" |
| S2 §6A.24 | "Multiplayer ist nicht Teil des minimalen Singleplayer-MVP" |
| S3 header | "Launch Anchor: Singleplayer Campaign; Online: public Multiplayer only after Gate" |
| S3 §48 | "50 Spieler ist kein Designargument. 50 Spieler ist ein Messziel." If quality is endangered: 50 → post-launch |

**Resolved.** The launch anchor is the **single-player campaign**. The
multiplayer *architecture* — server authority, replication model, protocol
versioning, server validation — is built from the start, because retrofitting
authority into a shipped single-player codebase is not feasible. Public
multiplayer ships only after the gate in [08](08-quality-gates.md).

Player count is a **measurement ladder, not a commitment**: 2 → 8 → 16 → 32,
with 50 as a separate stretch gate. 50 players is a measurement target. If it
endangers product quality it moves post-launch without architectural loss.

**This supersedes an earlier draft of chapter 00** which listed "dedicated
server matches of up to 50 players" as a binding production goal. Three of the
four source positions contradict that, so it was wrong.

## C2 — Gem count and PhoenixAnimation

| Source | Position |
| --- | --- |
| S1 §5, §9 | Eight gems: Core, Gameplay, Character, AI, World, Presentation, Networking, Tools |
| S3 §8.1 | Nine gems — adds **PhoenixAnimation** |
| S3 §8.2 | PhoenixTelemetry, PhoenixSimulation "optional, only if the split brings a real build, ownership or dependency advantage" |
| S2 §6A-P0-03 | Six gems minimum; AI and Networking may start minimal |

**Resolved.** **Eight gems**, as S1 lists them. Animation control lives in
`PhoenixPresentation`; EMotionFX remains the animation runtime.

The reason comes from S3 itself: §8.3 argues *against* gem proliferation
(build complexity, descriptor complexity, dependency management, ownership
problems, longer iteration). Adding a ninth gem whose only content is
animation *control* — a few hundred lines that read movement state and write
animation parameters — buys none of the three advantages §8.2 requires.
`PhoenixTelemetry` and `PhoenixSimulation` are likewise not created.

S2's six-gem start is compatible: the eight gems exist structurally, and AI and
Networking are thin until their MVP phase.

## C3 — PhoenixTools dependencies

| Source | Position |
| --- | --- |
| S1 §9.8 | PhoenixTools depends on PhoenixCore + Editor/AzToolsFramework |
| S1 §142 | The ASCII dependency graph draws PhoenixTools **above everything**, depending on Networking, Presentation and AI |

S1 contradicts itself here. **Resolved** in favour of §9.8, the explicit
dependency list: `PhoenixTools` depends on `PhoenixCore` and the editor
framework only.

Reason: a tools gem that depends on every runtime gem cannot be built for a
tools-only configuration, and it makes every runtime change rebuild tooling.
The §142 graph is read as an informal "tools sit outside the runtime stack"
sketch, not as a dependency declaration.

## C4 — ADR numbering

Three incompatible schemes were supplied:

| Source | Scheme |
| --- | --- |
| S1 §89 | ADR-0001 O3DE Baseline, 0002 Gem Architecture, 0003 Physics Ownership, 0004 **Character Architecture**, 0005 Rendering Extension Policy, 0006 **Save Architecture**, 0007 **Networking Authority**, 0008 World Streaming, 0009 AI Architecture, 0010 Performance Budgets, 0011 Engine Fork Policy |
| S3 §81 | ADR-001 O3DE 26.05 baseline, 002 **PhysX 5**, 003 **EMotionFX**, 004 **Multiplayer Gem**, 005 **Dedicated Server**, 006 **Singleplayer launch anchor**, 007 World streaming model, 008 Save schema, 009 Rendering extension policy, 010 Engine fork policy |
| Repository | ADR-0001 O3DE Baseline, 0002 Gem Architecture, 0003 Physics Ownership, 0004 **Save**, 0005 **Network Authority** |

Collisions: ADR-0004 means Character Architecture (S1), Multiplayer Gem (S3)
and Save (repo). ADR-0005 means Rendering (S1), Dedicated Server (S3) and
Network Authority (repo).

**Resolved.** The repository's existing numbers 0001–0005 are **kept**, because
they are already committed and referenced; renumbering committed ADRs would
invalidate every existing citation. New decisions continue from 0006. The
canonical register is `docs/adr/README.md`.

## C5 — Project file-list naming

| Source | Position |
| --- | --- |
| S1 §110, §130 | `project/Code/Phoenix_files.cmake` (manual sources), `Phoenix_autogen_files.cmake` (generated), `enabled_gems.cmake` (gem activation) — "diese drei Verantwortlichkeiten dürfen nicht vermischt werden" |
| Engine requirement | A gem/project with both a static library and a loadable module needs its manual sources split into api / private / shared lists |

**Resolved.** The *rule* is honoured exactly: manual sources, generated files
and gem activation remain three separate responsibilities in three separate
places. The *single filename* is not, because one flat list cannot feed two
targets: the module must carry only the module entry point, or it duplicates
every symbol in the static library.

Manual sources are therefore `phoenix_api_files.cmake`,
`phoenix_private_files.cmake` and `phoenix_shared_files.cmake`.
`Phoenix_autogen_files.cmake` and `enabled_gems.cmake` are untouched and
remain separate. See [02 — Architecture](02-architecture.md).

## C6 — Server tick rate

No source states a tick rate. An earlier draft of chapter 04 asserted 30 Hz as
though it were decided.

**Resolved as OPEN.** The tick rate is a measured outcome, not an assumption:
S3 §54 requires a tick target, warning and hard limit derived from profiling,
and S3 §50 states budgets are fixed against reference hardware. Recorded as
**OPEN** in [07 — Budgets](07-budgets.md). Owner: Engineering. Target: the
Performance Baseline milestone (M5).

## C7 — Launch scope needed a classification, not a list

Production Bible v3.2 §1.1 organises every feature as **Must-have /
Should-have / Post-Launch**, with two governance rules S1–S3 lack: a
Should-have may not endanger a Must-have, and a Should-have becomes
Post-Launch *automatically* after endangering two consecutive milestones.
v3.2 §23.2 adds that a Post-Launch feature may not survive as a hidden
dependency inside a Must-have system.

**Adopted** as [11 — Launch Scope](11-scope.md). This refines C1 rather than
contradicting it: v3.2 names **16–32 players as the credible launch target**
with 50 a stretch test, which is more specific than the ladder C1 recorded.

## C8 — PhysX is not deterministic, and reconciliation must not assume it is

Production Bible v3.0 §9 states that O3DE documents PhysX 4.1 as the default
with PhysX 5 as an optional configuration, and that O3DE's PhysX simulation is
not generally deterministic. Its conclusion: server authority plus prediction
and reconciliation, **not** deterministic PhysX rollback.

**Adopted, and it corrected an error.** An earlier revision of
[04 — Multiplayer](04-multiplayer.md) required that "simulation must be
deterministic", which read as a guarantee the physics engine does not offer.
The requirement is now scoped to Phoenix's own movement rules, with an
explicit statement of what reconciliation may not assume, and
physics-driven objects are server-authoritative rather than predicted.

The same paragraph independently corroborates the gem finding in
[ADR-0010](../adr/0010-engine-dependency-verification.md): the gem named
`PhysX` is PhysX 4, and PhysX 5 is separate.

## C9 — The frame target was decided all along

v3.2 states **stable 60 FPS on the defined reference hardware** as a
Must-have, with 120 FPS a should-have on strong hardware, and that frame-time
*stability* outranks average frame rate.

**Adopted.** [07 — Budgets](07-budgets.md) previously carried every value as
OPEN, including the frame total. The total is now set (16.67 ms) and
`budgets.json` carries it. Its distribution across areas, the warning and
critical thresholds, and the reference hardware specification itself remain
OPEN — a 60 FPS figure means nothing until the hardware it applies to is
named.

## C10 — There is no single tick rate

v3.0 §21 and v3.2 separate six rates — input, simulation, replication,
snapshot, render, interpolation — and explicitly reject the claim that a
higher uniform rate is always better.

**Adopted** into [07 — Budgets](07-budgets.md). C6 remains correct that the
rate is a measured outcome; v3.0 adds that it is six measurements, not one.

## Contributions adopted without conflict

Also taken from the superseded revisions, because each is more concrete than
what S1–S3 carried:

- **Severity classes S0–S4** for release decisions, in
  [11 — Launch Scope](11-scope.md). S0 blocks deployment, S1 blocks release,
  S2 needs a three-way decision.
- **Forbidden cross-cutting dependencies** (rendering → gameplay rules,
  audio → network authority, UI → PhysX internals, asset pipeline → runtime
  gameplay, client presentation → server persistence, gameplay data → engine
  internals), in [02 — Architecture](02-architecture.md).
- **Interest-management priority levels 0–4**, in
  [04 — Multiplayer](04-multiplayer.md), replacing a generic "priority"
  mechanism.
- **The multiplayer decision gate** with its two explicit paths and their
  prerequisites, in [09 — Roadmap](09-roadmap.md).
- **The production phase model** with per-phase gates, in the same chapter.

### Not adopted: the larger gem sets

v1.0 §5.2 lists fourteen gems (adding `PhoenixCombat`, `PhoenixPhysics`,
`PhoenixRendering`, `PhoenixAudio`, `PhoenixUI`, `PhoenixTelemetry`,
`PhoenixAnimation`); v3.0 and v3.2 list eleven to twelve. The eight-gem set
stands, per **C2**: S3 §8.3 argues against gem proliferation, and these
revisions are superseded. Combat lives in `PhoenixGameplay`, rendering and
audio integration in `PhoenixPresentation`, physics rules in
`PhoenixCharacter` and `PhoenixWorld` over the engine's PhysX gem.

This is recorded rather than silently dropped, because the split is a
reasonable future decision — it is a *cost* decision, not a correctness one,
and the tier table in [02](02-architecture.md) would accommodate it.

## Non-conflicts worth recording

These appear in several sources and agree; they are listed so nobody
re-litigates them:

- **No parallel engine.** No custom ECS, renderer, physics, animation runtime,
  network protocol, asset pipeline, UI framework or build system. S1 §3.1,
  S3 §0.1.
- **No invented O3DE APIs.** Phoenix names are never presented as engine
  names. S1 §138, §151.16; S3 §6.
- **Generated files are never hand-edited.** S1 §55, §106; S3 §41.
- **No second gem-activation mechanism.** `enabled_gems.cmake` is O3DE-managed
  via `o3de enable-gem`. S1 §7, §151.18.
- **Presentation observes simulation** and never mutates it. S1 §144; S3 §5.
- **Combat is specified as abstract game mechanics only**; no real-world
  weapon construction, procurement, modification or ballistic optimisation.
  S3 §24, and the explicit boundary in the project brief. See
  [README](README.md) and [03](03-runtime-systems.md).
