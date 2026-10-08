# 09 — Engineering Sequence and MVP Backlog

## The implementation rule

Not every file named in this document is written on day one. Files fall into
three classes:

| Class | Meaning |
| --- | --- |
| **A — Source required** | written by hand, now |
| **B — Generated** | produced by the engine or a tool; never hand-edited |
| **C — Conditional** | created when the feature needs it |

This exists to stop the repository becoming thousands of empty files. A Class C
file absent from the tree is correct, not missing.

## Required-first file set

The genuinely required set, which the repository now carries:

```
project/project.json
project/CMakeLists.txt
project/Code/CMakeLists.txt
project/Code/phoenix_{api,private,shared}_files.cmake   (see C5 in chapter 90)
project/Code/Phoenix_autogen_files.cmake
project/Code/enabled_gems.cmake                        (O3DE-managed)

gems/Phoenix{Core,Gameplay,Character,AI,World,Presentation,Networking,Tools}/
    gem.json
    CMakeLists.txt
    Code/CMakeLists.txt
    Code/{gem}_{api,private,shared}_files.cmake
    Code/Platform/{Windows,Linux}/platform_{platform}_files.cmake

scripts/{configure,build,test,validate,check_cmake,package,clean,generate_manifest,release}.py
tests/Unit/
```

Everything else grows along the backlog below.

## Dependency order

Implementation follows dependencies, not the alphabet:

```
PHASE 0   Project + Engine + Gems + CMake
PHASE 1   Core + Diagnostics + Input
PHASE 2   Character + Camera + PhysX + Movement
PHASE 3   Gameplay + Actions + State + Feedback
PHASE 4   Animation + Audio + UI + VFX
PHASE 5   World + Prefabs + Navigation + AI
PHASE 6   Mission + Objective + Save
PHASE 7   Streaming + Performance + Validation
PHASE 8   Vertical Slice
PHASE 9   Multiplayer Prototype
PHASE 10  Production + Alpha + Beta + RC + Gold
```

## Critical path

```
Project -> Build -> Character -> Movement -> Gameplay -> AI
        -> Mission -> Save -> Vertical Slice
```

Anything not supporting this path may not slow it down.

## First 12–16 weeks

Week numbers are sequence, not a commitment to a calendar; each week's exit
criterion is what matters.

| Week | Work | Exit criterion |
| --- | --- | --- |
| 1 | Register engine; confirm the unverified values in `docs/implementation/verified-boundaries.md` (engine gem names, setreg root, licence); reference hardware spec | `o3de enable-gem` succeeds for every declared gem; `verified-boundaries.md` has no open items |
| 2 | Configure + compile the full gem set; launcher boots | **M0 Bootable** — application starts reproducibly |
| 3 | Asset pipeline end to end: one mesh, material, texture, animation, prefab | A source asset reaches the runtime as a product asset |
| 4 | Diagnostics: logging, assertions, build id, version reporting; automated smoke test | Smoke test (launch→load→spawn→move→exit) runs in CI |
| 5 | Input mapping and first-person camera | Look/move stable; no transform dependency on UI or renderer |
| 6 | Character entity + PhysX character controller | Walk, collide, gravity, slope, step — no transform teleportation |
| 7 | Movement state machine (Idle/Walk/Sprint/Crouch/Jump/Fall/Disabled) | **M1 Controllable** — a test area is reliably controllable |
| 8 | Movement feel tuning; movement profile as data | No magic numbers in movement code |
| 9 | Interaction + action system (request → precondition → authority → execution → result) | One full interaction works end to end |
| 10 | Gameplay result, health/state, feedback (animation + audio + VFX) | **M2 Playable** — simulation→presentation loop validated |
| 11 | EMotionFX integration; gameplay→animation parameters; basic IK | Animation reads movement state and never writes it |
| 12 | Prefab world, world activation, navigation mesh | Asset-loaded, world-active and gameplay-active are distinct |
| 13 | AI agent, perception, knowledge, decision | **M3 Reactive** — the world reacts to the player |
| 14 | Encounter, objective, mission state | A mission can be completed |
| 15 | Save schema, SaveData integration, load/continue, one migration test | **M4 Complete** — play→save→quit→reload→continue restores state |
| 16 | Performance baseline, asset validation, debug views, automated gameplay tests | **M5 Production-Ready Slice** — another team member can play and validate it without a developer workaround |

Multiplayer prototype work begins after M5, not before — see
[90](90-source-reconciliation.md) C1.

## Milestones

| Milestone | Gate |
| --- | --- |
| M0 Bootable | application starts reproducibly |
| M1 Controllable | player reliably controls a test area |
| M2 Playable | one complete gameplay interaction works |
| M3 Reactive | the world reacts to the player |
| M4 Complete | a mission can be completed and resumed |
| M5 Production-Ready Slice | playable and validatable by a non-developer |
| M6 MVP | all M0–M5 gates passed |

## Priority model

| Priority | Meaning |
| --- | --- |
| P0 | existential — no working MVP without it |
| P1 | core product — no convincing FPS MVP without it |
| P2 | production-relevant — required for the vertical slice |
| P3 | quality — after a working slice |
| P4 | stretch / later |
| X | explicitly excluded |

Order is P0 → P1 → P2 → P3 → P4. **A lower-priority feature may not block a
higher-priority one.**

| Area | P0 | P1 | P2 | P3 | P4 |
| --- | --- | --- | --- | --- | --- |
| Engine / Build | ✓ | | | | |
| Core | ✓ | | | | |
| Input | ✓ | | | | |
| Character | ✓ | ✓ | | | |
| Movement | ✓ | ✓ | | | |
| Physics | ✓ | ✓ | | | |
| Animation | | ✓ | ✓ | ✓ | |
| Gameplay | | ✓ | ✓ | | |
| AI | | ✓ | ✓ | | |
| World | | ✓ | ✓ | | |
| Mission | | ✓ | ✓ | | |
| Save | | ✓ | ✓ | | |
| Rendering | ✓ | ✓ | ✓ | ✓ | |
| Audio / VFX / UI | | ✓ | ✓ | ✓ | |
| Validation | ✓ | ✓ | ✓ | | |
| Performance | ✓ | ✓ | ✓ | ✓ | |
| Tools | ✓ | ✓ | ✓ | ✓ | |
| Accessibility | | | ✓ | ✓ | |
| Multiplayer | | | | | ✓ |
| Backend | | | | | ✓ |

## Explicitly excluded from MVP

50-player production, full matchmaking, cross-platform, clans, ranked, live
operations, replay, spectator, large persistent world, complex destruction,
advanced ray tracing, large-scale volumetrics, full backend ecosystem,
advanced social systems.

These can follow from a stable core product. They are not architectural debt;
they are deferred scope.

## Backlog item format

Every backlog item carries: id, priority, owner, dependencies, estimate, risk,
acceptance criteria, test, performance impact, status.

```
MVP-P0-11  Character Controller
Priority:      P0
Dependencies:  PhoenixCore, PhysX, Input
Owner:         Character
Acceptance:    Player can walk, sprint, jump and collide
               without transform teleportation.
Tests:         movement integration, collision, regression
Performance:   measured CPU / physics cost
```

## Backlog rules

1. No P3 feature may mask a P0/P1 problem.
2. No art pass before gameplay validation.
3. No multiplayer feature may destabilise the single-player MVP.
4. No engine fork for an MVP problem while project code or an O3DE-conformant
   approach suffices.
5. No performance optimisation without measurement.
6. No new abstraction without concrete benefit.
7. Every MVP system needs at least one reproducible test.
8. A feature that lengthens the critical path must justify itself explicitly.

## MVP golden rule

The MVP is not judged by the number of systems implemented. It is judged on
whether the core loop is stable:

```
player -> input -> movement -> action -> world -> AI
       -> objective -> mission -> save -> reload
```

Ten additional working systems with an unstable core loop is not an MVP.
