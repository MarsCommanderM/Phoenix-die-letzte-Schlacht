# 03 — Runtime Systems

All simulation state is owned by the server in multiplayer and by the local
simulation in single-player. Every system below reads simulation state;
`PhoenixPresentation` may only read it.

## Movement and character

Owner: `PhoenixCharacter` (tier 2).

Movement is a deterministic state machine over a fixed simulation step. The
state set is declared in `Phoenix/Character/PhoenixMovementTypes.h`:
`Idle, Walk, Sprint, Crouch, Slide, Jump, Fall, Mantle, Vault, Disabled`.

| Property | Decision |
| --- | --- |
| Simulation step | Fixed; movement never integrates against a variable frame delta |
| Input | `NetworkInput` from the Multiplayer Framework; never read directly from devices in simulation code |
| Collision | PhysX 5 character controller; Phoenix owns the gait rules, not the sweep |
| Authority | Server; client prediction is explicitly approved for movement (see [04](04-multiplayer.md)) |
| Animation coupling | One-way: movement state drives animation, animation never drives movement |

The last row is the rule most likely to be violated under art pressure. An
animation-driven position is not reproducible on the server, so it cannot be
reconciled; the request is to be refused and solved with a presentation-only
offset instead.

**OPEN** — gait tuning values (speeds, acceleration curves, slide and mantle
windows) are gameplay data, not architecture. Owner: Gameplay. Target: Week 6.

## Animation

Owner: `PhoenixPresentation` (tier 3), consuming `PhoenixCharacter` state.

EMotionFX drives skeletal animation. The animation graph consumes movement
state and velocity and produces pose only. Procedural layers (recoil sway,
look-at, foot placement) are presentation-side and must be deterministic
functions of simulation state plus time, so that two clients observing the
same simulation see the same pose.

## World and streaming

Owner: `PhoenixWorld` (tier 2).

The world is divided into cells (`Phoenix/World/PhoenixWorldCell.h`:
id, bounds, `gameplayActive`). Streaming is asynchronous and cell-based.

| Property | Decision |
| --- | --- |
| Granularity | Cell, with an explicit `gameplayActive` flag separating "loaded" from "simulating" |
| Loading | Asynchronous; a synchronous load on the game thread is a defect, not a slow path |
| Budget | Streaming must not produce frame-time spikes above the budget in [07](07-budgets.md) |
| Server | The server streams gameplay-relevant cells for all 50 players, which is a different working set from any single client |

The separation of loaded from gameplay-active exists because the server's
relevant set is the union over all players, while a client's is its own
neighbourhood. Conflating them is the most direct path to the scaling risk in
[10](10-risks.md).

## AI

Owner: `PhoenixAI` (tier 3).

`Phoenix/AI/PhoenixAIState.h` declares `Idle, Investigate, Navigate, Act,
Suspended`; `PhoenixAIContext.h` carries position, threat and confidence.

| Property | Decision |
| --- | --- |
| Authority | Server only. AI never runs on clients. |
| Budget | AI shares the server tick budget with replication and physics; see [07](07-budgets.md) |
| Suspension | `Suspended` is a first-class state: AI in non-gameplay-active cells costs nothing |
| Navigation | Engine navigation; Phoenix owns behaviour, not pathfinding |

`Suspended` is listed as a decision rather than an optimisation because a
50-player streaming world cannot afford agents that tick everywhere.

## Audio

Owner: `PhoenixPresentation` (tier 3).

Audio observes simulation events (`Phoenix/Presentation/PhoenixPresentationEvent.h`:
position, intensity). Audio never gates gameplay: a sound that fails to load
must not delay or alter a simulation step.

**OPEN** — middleware choice and bus layout. Owner: Audio. Target: Week 8.

## Combat layer

Owner: `PhoenixGameplay` (tier 1), with authority rules from
`PhoenixNetworking`.

Specified **as abstract game mechanics only**, per the boundary in the
[document scope](README.md). What that means concretely:

| Element | Specification |
| --- | --- |
| Action model | `Phoenix/Gameplay/PhoenixAction.h`: an id, a duration and a cooldown. Actions are data, not code. |
| Authority | The server validates every action: cooldown elapsed, actor state permits it, target resolvable. A client-asserted outcome is never trusted. |
| Hit resolution | Server-side, against the server's view of the simulation, reconciled against the actor's acknowledged input time |
| Damage | An event carrying actor, target, amount and cause. Health is server state. |
| Tuning | Spread, recoil and falloff are curves in data assets, authored and balanced for game feel and competitive fairness |
| State | Per-actor combat state is a state machine like movement: explicit, enumerable, server-owned |

This document specifies no real-world weapon behaviour, construction,
modification or ballistic tuning. The numbers in the tuning curves are
gameplay values validated by playtest and balance review; they are not
physical specifications and must not be presented as such.

## Cross-system communication

Systems communicate through:

1. **Interfaces** on tier boundaries — see `docs/implementation/interfaces.md`.
2. **Events** for fire-and-forget notification, always simulation → presentation.
3. **Versioned data assets** for tuning and content — see [06](06-data-schemas.md).

Direct calls across a tier boundary in the wrong direction are rejected by
`scripts/validate.py` at the manifest level and by review at the code level.
