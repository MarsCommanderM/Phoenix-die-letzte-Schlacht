# Multiplayer Component Schemas

Network components are declared as AutoComponent XML in
`project/Code/Source/AutoGen/` and compiled by O3DE Multiplayer into C++
components and controllers.

```
XML -> O3DE Multiplayer code generation -> generated C++ -> CMake -> compile -> runtime
```

Generated `*.AutoComponent.h`, `*.AutoComponent.cpp` and `AutoComponentTypes.*`
are build products. They are **never committed and never hand-edited**. After
changing an XML: reconfigure → regenerate → compile → run network tests.

The XML list lives in `project/Code/Phoenix_autogen_files.cmake`, which holds
generated-file inputs only. Manual sources
(`phoenix_{api,private,shared}_files.cmake`) and gem activation
(`enabled_gems.cmake`) stay separate.

## Data-model categories

Each piece of replicated information belongs to exactly one category:

| Category | Use | Example |
| --- | --- | --- |
| `NetworkInput` | client intent for a simulation step | move, look, jump, crouch |
| `NetworkProperty` | continuously replicated state | movement state, health, objective state |
| RPC | discrete event | mission completed, objective event |
| Local | never replicated | camera shake, local presentation |
| Server-validated | client request the server adjudicates | action request, score |

**RPC is not a substitute for continuous state**, and a property is not
replicated out of convenience: each one costs a budget line
(`docs/tdd/07-budgets.md`) and needs an authority rule
(`docs/tdd/04-multiplayer.md`).

## Declared components

| Component | Carries | Authority |
| --- | --- | --- |
| `PhoenixNetworkPlayerComponent` | `NetworkInput`: MoveForward, MoveRight, Jump, Crouch | client input → server |
| `PhoenixNetworkCharacterComponent` | MovementState, Velocity, Grounded | server; movement prediction approved |
| `PhoenixNetworkGameplayComponent` | Health, GameplayState | server; prediction forbidden |
| `PhoenixNetworkObjectiveComponent` | ObjectiveState | server; prediction forbidden |
| `PhoenixNetworkWorldComponent` | CellActivation | server |

## Input pipeline

```
device -> input capture -> CreateInput -> network tick -> ProcessInput -> simulation
```

This pipeline is what makes prediction possible: the same input sequence
replayed from the same start state must produce the same result, which is why
movement uses a fixed simulation step.

## Not yet verified

The **attribute sets** on `NetworkProperty` (`ReplicateFrom`, `ReplicateTo`,
`Container`) follow the documented AutoComponent model but have **not** been
validated against the O3DE 26.05.0 AutoComponent schema, because no engine is
registered in the environment where these files were authored.

First action on a registered engine: run the generator and fix any attribute
rejected by the engine's schema. Tracked in
`docs/implementation/verified-boundaries.md`.
