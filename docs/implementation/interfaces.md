# Interface Contracts

Every public Phoenix interface documents nine things. An interface missing any
of them is not accepted into production — see
`docs/tdd/08-quality-gates.md`.

| Field | Why it is mandatory |
| --- | --- |
| Purpose | an interface without a stated purpose accumulates unrelated methods |
| Inputs | |
| Outputs | |
| Ownership | who may change it |
| Lifetime | when the object is valid |
| Thread context | no system may assume it is always on the main thread |
| Failure mode | what a caller sees when it fails |
| Performance expectation | so a caller can budget for it |
| Version | so a change is detectable |

## Phoenix API versus O3DE API

These names are **O3DE** APIs and may be described as engine interfaces:

`AZ::Component`, `AZ::TickBus`, `AZ::EBus`, `AZ::TransformBus`,
`PhysX::CharacterControllerComponent`, `PhysX::RigidBodyComponent`,
`PhysX::RagdollComponent`, `EMotionFX::Integration::ActorComponent`,
`EMotionFX::Integration::AnimGraphComponent`, `AZ::RPI::Pass`,
`SaveData::SaveDataSystemComponent`, Multiplayer AutoComponents,
`NetworkInput`, `NetworkProperty`, RPC, `CreateInput`, `ProcessInput`.

These names are **Phoenix** project APIs and must never be presented as engine
interfaces:

`PhoenixMovementComponent`, `PhoenixGameplayState`, `PhoenixPhysicsQuery`,
`PhoenixMissionComponent`, `PhoenixTraversalComponent`, `PhoenixWorldState`,
`PhoenixNetworkPolicy`, `PhoenixSaveService`, `PhoenixTelemetryService`,
`PhoenixWorldCell`, `PhoenixAIContext`.

Before writing a Phoenix abstraction: search the O3DE API, check the gem
reference, check the user guide, check the existing component path. This
ordering is what prevents invented engine APIs.

## Tier-boundary contracts

### Movement → Animation

| Field | Value |
| --- | --- |
| Purpose | drive animation from simulation state |
| Inputs | `MovementState`, velocity, stance |
| Outputs | animation parameters |
| Ownership | Animation (consumer) owns the mapping; Character owns the state |
| Direction | **one-way.** Animation never writes movement state |
| Thread context | simulation update |
| Failure mode | fall back to base locomotion; never block the simulation step |
| Version | 1 |

The one-way rule is load-bearing: an animation-driven position is not
reproducible on the server and therefore cannot be reconciled.

### Gameplay → Presentation

| Field | Value |
| --- | --- |
| Purpose | notify presentation of simulation outcomes |
| Inputs | domain events (objective completed, character disabled, impact result) |
| Outputs | presentation events (play VFX, play audio, camera response) |
| Direction | **one-way.** Presentation never mutates gameplay |
| Failure mode | a missing optional effect is `Degraded`, never `Fatal` |
| Version | 1 |

### Gameplay → Physics query

`PhoenixPhysicsQuery` standardises gameplay-side queries: ray, sphere, capsule,
box, sweep, overlap — each with query type, collision layer, collision mask,
filter, distance and debug mode.

It is a Phoenix abstraction over O3DE PhysX. It does **not** replace PhysX, and
Phoenix defines no second character controller.

### Save

`PhoenixSaveService` is an adapter and orchestrator. It owns neither the
schema serialisation format's platform details nor the file I/O:

```
PhoenixSaveService -> Phoenix Save Schema -> O3DE SaveData -> Platform
```

## Event categories

Three categories, never mixed:

| Category | Examples |
| --- | --- |
| Domain event | `ObjectiveCompleted`, `MissionStarted`, `CharacterDisabled` |
| Presentation event | `PlayVFX`, `PlayAudio`, `CameraResponse` |
| Network event | replication, RPC, network input |

## EBus policy

EBus is for stable service, request and notification interfaces — not for
everything:

| Need | Mechanism |
| --- | --- |
| local collaboration | direct reference or local structure |
| stable service / engine interface | EBus |
| one-off occurrence | event / notification |

## Tick policy

No artificial global Phoenix tick with an invented ordering. The flow is:

```
input -> command -> simulation -> state -> events -> presentation
```

`AZ::TickBus` is used only where a system genuinely works per tick.

## Thread model

Threads a contract may name: main, worker, physics, render, audio, network.

Each system documents which thread its work happens on. **There is no implicit
thread safety**, and cross-thread data is synchronised explicitly.
