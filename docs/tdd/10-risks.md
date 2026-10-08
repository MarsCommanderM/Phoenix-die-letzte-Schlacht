# 10 — Risk Register

Every risk carries: id, probability, impact, owner, mitigation, trigger,
deadline, status. Priority: Critical / High / Medium / Low.

A risk without a **trigger** is not managed — the trigger is the observable
condition that says the risk is materialising now, rather than a feeling that
it might.

## The three largest

### R01 — Multiplayer and simulation scaling · Critical

Players, AI, physics, streaming and replication can saturate server tick, CPU,
bandwidth and memory *simultaneously*, which is what makes this the top risk:
each is individually survivable and they arrive together.

- **Mitigation.** Climb the player ladder by measurement (2→8→16→32); interest
  management with a hard per-client replication cap; replication budgets;
  server profiling; soak tests from the Foundation phase.
- **Trigger.** Server tick variance exceeds its warning band at any rung, or
  bandwidth per player grows with world content rather than player count.
- **Owner.** Online / Engineering.

### R02 — Streaming and rendering stutter · Critical

World streaming, shader variants, GPU uploads, temporal effects and volumetric
systems can produce unpredictable frame-time spikes. Spikes, not averages, are
what players feel.

- **Mitigation.** Asynchronous cell-based streaming; deterministic shader
  builds; variant limits in CI; fixed measurement scenes; automated
  performance regressions with baselines and thresholds.
- **Trigger.** Any frame-time spike above the critical threshold in a
  measurement scene, or a cell load that transitively pulls unrelated content.
- **Owner.** Rendering / Engineering.

### R03 — Architecture and production complexity · Critical

A growing engine fork, strong system coupling or uncontrolled feature scope
can jeopardise upgrades, debugging, content production and release planning.

- **Mitigation.** Architecture reviews on every PR ([08](08-quality-gates.md));
  machine-enforced acyclic gem dependencies; documented owners; feature gates;
  versioned data; a binding definition of done.
- **Trigger.** The fork patch count grows in a release without an ADR, or a
  dependency-direction violation reaches review rather than being caught by
  `scripts/validate.py`.
- **Owner.** Engineering.

## Full register

| ID | Risk | Priority | Primary mitigation |
| --- | --- | --- | --- |
| R01 | Multiplayer scaling | Critical | measurement ladder, interest management, replication caps |
| R02 | Streaming stutter | Critical | async cell streaming, measurement scenes, regression gates |
| R03 | Architecture / production complexity | Critical | reviews, enforced tiers, owners, DoD |
| R04 | Scope explosion | Critical | scope gates MUST/SHOULD/EXPERIMENTAL/POST/REJECTED; one classification per feature |
| R05 | Engine fork growth | High | ADR per patch; patch set reviewed at every upgrade |
| R06 | Memory growth | High | per-area target/warning/hard limit; soak tests |
| R07 | Shader variant explosion | High | variant approval gate; CI count ceiling |
| R08 | AI CPU cost | High | update-frequency tiers; `Suspended` state; per-agent budgets |
| R09 | Animation complexity | Medium | animation LOD tiers; one-way gameplay→animation coupling |
| R10 | Asset production throughput | Medium | automated validation; throughput metrics; rework tracking |
| R11 | Save migration | Medium | versioned schema; deterministic, tested migrations |
| R12 | Tooling deficiency | Medium | tools treated as product; automate any repeated manual process |
| R13 | Backend coupling | Medium | backend outside the simulation; server never blocks on backend for gameplay decisions |

## Scope gates

Each feature carries exactly one classification: `MUST`, `SHOULD`,
`EXPERIMENTAL`, `POST`, `REJECTED`.

A feature moves up one level only on demonstrated value, technical readiness,
production capacity, performance and QA. **No feature becomes a must-have
because work has already started on it** — sunk cost is not a classification
criterion.

## Prototype rule

A prototype may be fast, ugly and incomplete. A prototype may **not** silently
become production architecture. Before production: prototype review → keep,
rewrite, merge or reject.

## Feature flags

`ExperimentalRendering`, `ExperimentalAI`, `ExperimentalTraversal`,
`MultiplayerPrototype`, `DebugVisualization`, `PostLaunchFeature`.

Release builds must contain no unintended experimental flags; this is checked,
not trusted.

## Temporary solutions

No temporary solution without an expiry date. A workaround without one becomes
permanent by default, which is how R03 materialises.
