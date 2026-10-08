# 08 — CI, Regression Testing and Release Gates

## Test pyramid

```
        E2E
      System
   Integration
       Unit
```

Plus dimension suites: performance, rendering, physics, animation, AI, world,
networking, save, asset, soak.

| Level | Covers |
| --- | --- |
| Unit | rules, math, state, serialisation, validation |
| Integration | character+physics, gameplay+world, mission+save, network+gameplay, animation+character |
| System | a whole subsystem against real data |
| E2E | the full product loop below |

## The E2E loop

The mandatory end-to-end test, which is also the MVP definition:

```
boot -> load -> spawn -> input -> movement -> gameplay -> objective
     -> mission complete -> save -> exit -> reload -> continue
```

This must work reproducibly, measurably and **without manual developer
intervention**. A slice that only works through special-case code is not a
valid production proof.

## CI pipelines

Workflows live in `.github/workflows/`, which is where GitHub runs them.

| Pipeline | Trigger | Runs |
| --- | --- | --- |
| `pull_request.yml` | every PR | static validation, repository tests, CMake structure check |
| `nightly.yml` | 02:00 daily | the above, plus full validation |
| `release.yml` | manual | the above, plus source manifest generation |
| `server.yml` | manual | server configuration validation |

Currently enforced on every pull request, with no engine required:

| Gate | Checks |
| --- | --- |
| `scripts/validate.py` | schema validity; sample data against schema; id/filename agreement; mission→objective references; gem tier direction; CMake deps vs `gem.json` |
| `scripts/check_cmake.py` | every CMake list file parses; every declared path exists; every `FILES_CMAKE`/`PLATFORM_INCLUDE_FILES` reference resolves |
| `scripts/test.py` | repository contract tests; **fails on an empty suite** |

The last clause matters: the imported starter's test runner reported success
while collecting zero tests. A gate that cannot fail is not a gate.

**Class C** — compile, asset processing, shader validation, rendering, physics,
AI, networking, performance and soak stages require a registered O3DE engine
and build agents, and are added as those land. Their place in the pipeline is
fixed here so they are not bolted on later:

```
Pull request:  configure -> compile -> unit -> integration
                         -> asset validation -> shader validation -> smoke
Nightly:       full build -> asset processing -> rendering -> physics
                          -> AI -> networking -> performance -> memory -> soak
```

## Regression tests

Every regression test carries a **baseline**, a **threshold**, an **owner** and
a **failure artefact**. Without the artefact a red CI run cannot be diagnosed,
and without an owner it is not fixed.

```
baseline GPU: X      current: X + delta      threshold: Y
delta > Y  ->  CI failure
```

Content regressions detected automatically: missing asset, broken reference,
invalid prefab, invalid material, missing LOD, missing collision, invalid
animation, invalid mission, invalid objective, invalid navigation.

## Soak tests

| Target | Durations |
| --- | --- |
| Client | 1 h, 4 h, 8 h |
| Server | 1 h, 4 h, 8 h, 24 h |

Monitored: memory, CPU, GPU, entity count, streaming, network, crashes.
A 24-hour server soak is required by acceptance criterion 5.

## Production gates

| Gate | Requires |
| --- | --- |
| A — Technology | build, renderer, physics, animation, character, asset pipeline |
| B — FPS Core | movement, camera, gameplay, AI, save |
| C — Vertical Slice | the full experience through one production pipeline |
| D — Content Production | pipeline proven at throughput |
| E — Alpha | feature complete |
| F — Beta | content complete |
| G — Release Candidate | no critical blockers |

**Neither full production nor content scaling may begin** before scaling,
streaming stability and architectural discipline are demonstrated through
gates A–C.

## The multiplayer gate

Public multiplayer is released only when **all** hold: server stable, network
stable, content ready, security ready, QA ready, campaign unaffected.

Otherwise multiplayer moves post-launch — without architectural loss, because
the authority model was built in from the start ([04](04-multiplayer.md)).

## Release blockers

Release is blocked by: crash; save corruption; broken progression;
unrecoverable soft lock; critical security issue; unbounded memory growth;
critical streaming failure; unstable build; critical accessibility failure;
missing required content; non-reproducible build; critical input failure.

Additionally, for online: authority failure, desync, replication failure,
protocol failure, server instability.

## Definition of Done

A feature is done only with: design, code, data, content, performance, QA,
telemetry and documentation. **A feature is not done because it works in the
editor.**

## Definition of Ready for production

A system may enter production when: API stable, data schema stable, tests
present, performance measured, owner assigned, failure mode defined, logging
present, documentation present, CI integrated.

**A system without an owner may not become production ready.**

## Architecture review

Every pull request answers:

1. Which layer changes?
2. Which dependency is added?
3. Is that dependency actually necessary?
4. Does O3DE functionality already exist for this?
5. Is the new API Phoenix-owned, and is it named as such?
6. Is persistence affected?
7. Is networking affected?
8. Is performance affected?
9. Which tests were added?

## API review

A new public Phoenix API is accepted only with: a use case, at least one real
consumer, clear ownership, clear lifetime, clear thread context, defined
failure behaviour, and a test. **No API "for later".**

Before writing one: search the O3DE API, check the gem reference, check the
user guide, check the existing component path — and only then add a Phoenix
abstraction. This is what prevents invented engine APIs.
