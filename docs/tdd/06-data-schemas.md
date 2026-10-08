# 06 — Data, Save and Protocol Schemas

## Three data classes

These are never mixed:

| Class | Edited by | Examples |
| --- | --- | --- |
| **Authoring** | Designers, artists | `MissionDefinition`, `ObjectiveDefinition`, `EncounterDefinition`, `ActionDefinition`, `TraversalDefinition` |
| **Runtime** | Nobody; derived | `RuntimeMission`, `RuntimeEncounter`, `RuntimeWorldCell` |
| **Persistent** | The player, indirectly | `CampaignSave`, `MissionSave`, `WorldStateSave`, `PlayerProgressSave`, `SettingsSave` |

No runtime component reads unvalidated authoring data directly:

```
Authoring -> Validation -> Asset Processing -> Product Asset -> Runtime -> Persistent State
```

## Schemas

JSON Schema files live in `project/Assets/Schema/` and validate authoring data.
They do not replace runtime types.

| Schema | Status |
| --- | --- |
| `action.schema.json` | present |
| `mission.schema.json` | present |
| `objective.schema.json` | present |
| `encounter.schema.json` | present |
| `save.schema.json` | present |
| `traversal.schema.json` | **Class C** — when traversal lands (P2) |
| `world_event.schema.json` | **Class C** |
| `localization.schema.json` | **Class C** |
| `configuration.schema.json` | **Class C** |

Class C means the file is created when the feature needs it, per the
implementation rule in [09 — Roadmap](09-roadmap.md). The repository does not
carry empty placeholder schemas.

`scripts/validate.py` enforces, for every present schema:

- the schema itself is a valid JSON Schema (draft 2020-12)
- every sample document under `project/Assets/Data/<Category>/` validates
  against its governing schema
- a document's `id` matches its filename
- cross-document references resolve (a mission referencing a missing objective
  fails the build)

## Typed identities

Strings are not the primary runtime identity. `PhoenixCore` declares:

`EntityId`, `CharacterId`, `ActionId`, `MissionId`, `ObjectiveId`,
`EncounterId`, `WorldCellId`, `SaveSlotId`, `NetworkObjectId`.

Reason: a string id typos silently and compares expensively. A typed id fails
at compile time.

## Result model

Every cross-system operation has an explicit outcome. `PhoenixResult`:

`Success, Failure, InvalidState, NotFound, Unavailable, Rejected, Timeout, Unsupported`.

No silent failure.

## Error classes

| Class | Example |
| --- | --- |
| Recoverable | telemetry upload failed; temporary network timeout |
| Degraded | optional VFX asset missing |
| Fatal | required mission data missing |

Not every error ends the session, and a missing optional effect must never be
treated as fatal.

## Save boundary

```
PhoenixSaveService  (Phoenix: adapter / orchestrator)
        |
Phoenix Save Schema  (Phoenix: versioned product contract)
        |
O3DE SaveData        (engine: buffers, request/notification bus)
        |
Platform persistence
```

`PhoenixSaveService` is an adapter. It does not own platform file I/O, and
O3DE SaveData is not replaced.

**Persisted:** header, schema version, campaign state, mission state,
objective state, world persistent state, player persistent state, settings,
progression, integrity.

**Never persisted:** GPU state, render history, temporary VFX, frame state,
transient caches, temporary animation pose, network prediction buffers.

The rule behind the second list: save is a public product contract. If it
depended on renderer or frame state, a renderer change would corrupt old
saves.

## Migration

```
V1 -> migration -> V2 -> migration -> current
```

Migrations are deterministic and tested. At least one migration test exists
from the first shipped schema version onward (MVP-P1-26).

## Independent version lines

Versioned separately, because they change at different rates:

engine version, project version, asset version, save schema, network protocol,
backend API.

```
old save   -> migration      -> current save
old client -> protocol check -> accept / reject
```

## Data contract per feature

Every significant gameplay feature carries: schema, authoring data, runtime
representation, validation, test data, migration strategy. A feature missing
any of these is not done — see [08](08-quality-gates.md).
