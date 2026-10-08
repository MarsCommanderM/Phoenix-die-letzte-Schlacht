# 04 — Server-Authoritative Multiplayer

Owner: `PhoenixNetworking` (tier 3).

## Scope

Public multiplayer is **not** part of the minimal single-player MVP. The
*architecture* below is built from the start, because server authority cannot
be retrofitted; the *feature* ships only after the multiplayer gate in
[08](08-quality-gates.md). See
[90 — Source Reconciliation](90-source-reconciliation.md) C1.

## Decision

Phoenix builds **on** the O3DE Multiplayer Framework, not beside it. The
framework provides server authority, entity replication, RPCs, local
prediction and backwards reconciliation. Phoenix adds the FPS-specific
relevance, priority and gameplay layer above it.

Re-implementing replication or reconciliation was removed from scope: it is
substantial cost with no product differentiation, and it would duplicate
functionality that the engine already tests.

## Authority model

`Phoenix/Networking/PhoenixNetworkPolicy.h` declares the authority set:
`Server, AutonomousClient, SimulatedClient, LocalOnly`.

| State class | Authority | Prediction |
| --- | --- | --- |
| Movement of the local player | Server | **Approved** — predicted locally, reconciled |
| Movement of other players | Server | Interpolated, never predicted |
| Combat outcome, health, score, inventory | Server | **Forbidden** |
| Persistent progression | Server, then backend | **Forbidden** |
| Cosmetic and presentation state | Client | Not applicable |

The rule behind the table: prediction is permitted only where a mispredict is
*visually* correctable. A mispredicted position is a small snap. A mispredicted
kill is unfixable — it has already been shown to the player as a fact.

Prediction for any state not listed as approved requires an ADR.

## Prediction and reconciliation

For approved state:

1. The client samples input into `NetworkInput` and applies it locally
   immediately.
2. The input is sent to the server with its frame identity.
3. The server simulates authoritatively and replicates the result.
4. The client compares the server result against its own prediction for that
   input, and on divergence re-simulates forward from the server state
   (backwards reconciliation).

Consequences that bind other systems:

- **Phoenix's own movement simulation** must be reproducible for a given input
  sequence and start state. This is why movement uses a fixed step
  ([03](03-runtime-systems.md)) and why animation must not drive position.
- Any simulation state that participates in prediction must be serialisable
  and rewindable.

### What reconciliation must not assume

Reconciliation is **not** a deterministic physics rollback. O3DE's PhysX
simulation is not documented as generally deterministic, and O3DE ships PhysX
4 as the default with PhysX 5 as a separate gem (which is why this project
declares `PhysX5`; see
[ADR-0010](../adr/0010-engine-dependency-verification.md)).

The model is therefore:

```
server-authoritative state  +  client prediction  +  correction
```

and **not**:

```
rewind the physics scene and re-simulate it identically
```

The correction **threshold** — how large a divergence must be before the
client is snapped rather than smoothed — is a measured value, not a chosen
one. A threshold picked by feel either corrects constantly (visible jitter on
a healthy connection) or too rarely (the client drifts). It is derived from
the network test matrix and recorded with the budgets in
[07](07-budgets.md); correction *count* is itself a telemetry metric, so a
badly set threshold is visible in the data rather than only in complaints.

Concretely: a correction replaces client state with server state and replays
the client's unacknowledged *inputs* through Phoenix's own movement rules. It
does not assume that re-running the PhysX scene from a restored snapshot
reproduces the same contacts. Any design that needs bit-identical physics
replay — lockstep, deterministic replay of physics-driven objects, rollback
netcode over rigid bodies — is out of scope and would need an ADR and a
different physics strategy.

This is also why physics-driven objects (ragdolls, debris, destruction) are
**server-authoritative state, not predicted**: their outcome cannot be
predicted reproducibly.

## Interest management

The server does not replicate everything to everyone. At 50 players this is
the difference between a working build and a saturated one.

| Mechanism | Purpose |
| --- | --- |
| Cell relevance | An entity in a cell no client has as gameplay-active is not replicated |
| Distance and visibility relevance | Per-client filtering within relevant cells |
| Priority | Explicit levels, highest first: **0** local player, **1** nearby players, **2** active objectives, **3** nearby world events, **4** distant state |
| Replication budget | A per-client per-tick cap on replicated state; exceeding it defers low-priority entities rather than growing the packet |

The budget is a hard cap, not a target. An uncapped replication set makes
bandwidth a function of world content, which cannot be load-tested
meaningfully.

Visibility alone does not determine relevance: a distant objective can be
gameplay-critical while a near prop is not. Relevance is computed from
distance, visibility, team relationship, objective relevance, audio relevance
and gameplay importance together.

## Component schemas

Network components are declared as AutoComponent XML under
`project/Code/Source/AutoGen/` and compiled by O3DE Multiplayer into C++.
Generated `*.AutoComponent.h/.cpp` are **not** committed; see
`gems/PhoenixNetworking/Code/Source/AutoGen/README.md`.

The schemas are specified in
`docs/implementation/multiplayer-components.md`.

## Server deployment

| Property | Decision |
| --- | --- |
| Server build | Dedicated, headless, Linux |
| Tick rate | **OPEN** — a measured outcome, not an assumption. See [07 — Budgets](07-budgets.md) |
| Players per server | **16–32 is the credible launch target**; the ladder is 2 → 8 → 16 → 32, with 50 a stretch test and a post-launch format if it is not stable |
| Validation | Every client-originated action validated server-side |
| Soak | 24-hour soak test required before release (acceptance criterion 5) |

## Network test matrix

Acceptance criterion 4 requires all of these to pass, not just the good case:

| Condition | Range |
| --- | --- |
| Latency | nominal, 100 ms, 200 ms, 300 ms |
| Jitter | 0, ±20 ms, ±60 ms |
| Packet loss | 0 %, 1 %, 5 % |
| Reordering | off, on |
| Player count | 1, 2, 4, 8, 16, 32 (50 only once that gate is opened) |

Latency steps are 0, 20, 50, 100, 150 ms with jitter, packet loss, reordering,
burst loss, and disconnect/reconnect, per the source test matrix.

The matrix is run against a fixed scenario so results are comparable between
builds. Prediction, reconciliation, interest management and server validation
must each hold across it.

**OPEN** — backend contracts for progression and matchmaking. Owner: Online.
Target: Week 12.
