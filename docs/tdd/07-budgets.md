# 07 — Performance, Memory and Network Budgets

## Principle

Performance is a resource budget and an architectural property, not a release
phase. It is measured from the first vertical slice onward.

**A budget without an automated check is treated as absent.** Every entry
below has five fields:

| Field | Meaning |
| --- | --- |
| Target | the value the build is expected to hold |
| Warning | deviation that raises a warning and notifies the owner |
| Critical | deviation that fails CI |
| Measurement | the scene and method producing the number |
| Owner | the person accountable for the number |

No optimisation without a measurement. No "it feels faster".

## Status

Concrete millisecond and megabyte values are set against **reference
hardware**, which is not yet fixed. Rather than invent numbers that would
later be cited as decisions, this chapter fixes the **structure, ownership and
enforcement** of the budgets and marks the values **OPEN**.

**Decided:** the client frame target is **stable 60 FPS on the defined
reference hardware** (16.67 ms), with 120 FPS a should-have on strong
hardware. Frame-time *stability* outranks average frame rate: a build that
averages 70 FPS with regular 40 ms spikes fails this target and a steady 60
passes it.

**OPEN** — the reference hardware itself. The 60 FPS figure is only meaningful
once the hardware it applies to is named. Owner: Engineering. Target: M1.

**OPEN** — warning and critical thresholds, and the per-area breakdown below.
Owner: per row. Target: M5 (Performance Baseline), measured, not estimated.

This is deliberate. A budget invented without a measurement scene is a number
nobody can defend in review, and it would make acceptance criterion 3
unfalsifiable.

## Client frame budget

The total frame budget decomposes; **no single team owns the whole frame**, and
the budget is centrally administered.

```
Total frame budget =
    Gameplay + Animation + Physics + AI + Rendering + Audio + Streaming + UI
```

Total frame budget: **16.67 ms** (60 FPS). The split across areas is OPEN —
the total is decided, its distribution is not.

| Area | Owner | Value |
| --- | --- | --- |
| Gameplay | Gameplay | OPEN |
| Animation | Animation/Presentation | OPEN |
| Physics | Engineering | OPEN |
| AI | AI | OPEN |
| Rendering | Rendering | OPEN |
| Audio | Audio | OPEN |
| Streaming | Engineering | OPEN |
| UI | UI | OPEN |

## Server tick budget

Measured per tick, decomposed:

simulation time, AI time, physics time, replication time, network time, and
**tick variance** — variance matters as much as the mean, because a tick that
is usually fast and occasionally triple-length produces the same player
experience as a consistently slow one.

Tick target, warning and hard limit: **OPEN** (see
[90 — Source Reconciliation](90-source-reconciliation.md) C6 — the rate is a
measured outcome, not an assumption).

**There is no single tick rate.** Six rates are measured and tuned
separately, and conflating them is how "just raise the tick rate" becomes a
performance decision nobody can evaluate:

| Rate | Governs |
| --- | --- |
| Input rate | how often client input is sampled |
| Simulation rate | the fixed step gameplay and movement advance on |
| Replication rate | how often state is sent |
| Snapshot rate | how often a full state snapshot is produced |
| Render rate | variable; decoupled from all of the above |
| Interpolation rate | how remote entities are smoothed between updates |

A blanket claim such as "128 Hz is always better" is rejected: each rate is
benchmarked against its own cost.

On exceeding the limit, in this order:

```
profile -> identify cost -> reduce frequency
                          | reduce scope
                          | optimise
                          +- reject feature
```

Buying hardware is not the first response.

## Memory budget

Per area, each with target / warning / hard limit: textures, meshes,
animations, audio, shaders, world, gameplay, streaming, physics, network.

## GPU budget

Separate budgets per pass group, matching the hierarchy in
[05](05-rendering.md): geometry, shadow, lighting, material, VFX, post,
volumetric, UI.

**A new visual effect requires a measured GPU entry before it is approved.**

## Streaming budget

Per world cell: resident memory, load time, unload time, dependencies,
priority.

Streaming must not produce uncontrolled cascades — a cell load that transitively
pulls in half the world is a defect regardless of its measured time.

## AI budget

Update frequency, perception frequency, path query budget, decision budget,
spawn budget.

Not every NPC runs full logic every tick; the `Suspended` tier in
[03](03-runtime-systems.md) exists for this.

## Network budget

Bytes/sec/player, packets/sec, entities/player, properties/entity, RPC
frequency, server replication CPU.

Also tracked: RTT, jitter, packet loss, correction count.

Network properties are **not** replicated out of convenience. Each replicated
property needs an authority rule ([04](04-multiplayer.md)) and a budget line.

Every multiplayer scene declares expected entity count, expected player count
and expected replication cost, so a scene can fail its own budget before it
reaches a load test.

## Shader variant budget

A hard ceiling on variant count, monitored in CI. See
[05](05-rendering.md) for the approval gate.

## Telemetry

Every metric carries: name, definition, unit, owner, sampling rate, retention,
alert threshold. A metric without these is not collected — this is what keeps
telemetry from becoming noise nobody reads.

Core technical metrics: FPS, frame time, CPU time, GPU time, memory, loading,
streaming, crashes, RTT, packet loss, server tick, replication cost.

Production metrics: build success rate, CI duration, crash rate, frame-time
regression, memory regression, asset failure rate.
