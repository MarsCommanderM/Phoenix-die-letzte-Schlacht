# 11 — Launch Scope

Phoenix is **not** treated as a simultaneous full production of campaign,
50-player multiplayer, several platforms and live operations. Every feature
carries exactly one of three classifications.

| Class | Meaning |
| --- | --- |
| **Must-have** | required for launch |
| **Should-have** | wanted, admissible only while it does not endanger a Must-have |
| **Post-Launch** | not part of the launch product; built after the launch is stable and evaluated |

The launch product is deliberately bounded: **a high-quality, stable PC
single-player campaign with a prepared multiplayer foundation.**

## The two governance rules

These are what make the classification more than a label:

1. **No Should-have may endanger a Must-have**, nor the campaign's quality,
   nor PC performance. No Post-Launch feature may consume production capacity
   that a Must-have needs before launch.
2. **A Should-have becomes Post-Launch automatically** when it endangers two
   consecutive milestones. This is not a discussion; it is the default, and
   keeping it requires an explicit decision with a named owner.

And one structural rule, which is checkable rather than cultural:

3. **A Post-Launch feature may not remain as a hidden dependency inside a
   Must-have system.** If the campaign cannot run without a feature that is
   officially Post-Launch, then either the feature is Must-have or the
   dependency is a defect.

## Matrix

| Area | Must-have | Should-have | Post-Launch |
| --- | --- | --- | --- |
| Platform | Windows PC, defined hardware matrix, keyboard/mouse | further PC GPU/CPU classes, ultrawide, controller config | consoles, cloud, handhelds, cross-platform, cross-progression |
| Campaign | full loop, missions, objectives, checkpoints, save/load + migration, one consistent ending, limited player choices | multiple endings, branching, consequence chains, optional missions | additional chapters, new arcs, co-op campaign |
| FPS core | movement, camera, character, animation, interaction, game rules | extended traversal set | — |
| Physics | character, world, ragdoll for central characters | limited cloth, limited destruction | large-scale destruction, vehicles, persistent world damage |
| Rendering | PBR, HDR/exposure, lighting, shadows, atmosphere, motion vectors, temporal reconstruction, quality presets | high-quality reflections, extended volumetrics, optional hardware ray tracing | full ray-tracing pipeline, experimental reconstruction |
| Multiplayer | **architecture** — dedicated server build, server authority, replication, validation, network diagnostics, prediction/reconciliation tests | **public launch** — one mode, limited maps, matchmaking, profiles, 16–32 players | 50 players as a public format, further modes, ranked, tournaments, social |
| Audio | dialogue, environment, movement, material interaction, ambience, spatial, occlusion/obstruction | extended HRTF, complex music states, MP audio relevance | full immersive simulation |
| UI / Accessibility | input remapping, subtitles, text scaling, colour options, motion reduction, camera-effect control, audio mixer, alternative visual feedback | extended layouts, presets, spectator UI | social UI, clans, leaderboards, live events |
| Production | reproducible builds, asset + build validation, crash reporting, technical telemetry, QA/performance/memory gates, release and rollback | campaign funnels, MP balance data, matchmaking quality | full live-ops analytics, seasonal KPIs, content experiments |
| Tools | profiler, asset validator, frame analyzer, world/animation/physics debuggers, performance HUD | network inspector, replication debugger (Must-have *for MP development*) | live-event editors, seasonal content tools, remote configuration |

## Multiplayer is two separate things

The distinction that the matrix above makes, and which the rest of this
document depends on:

- The multiplayer **architecture** is Must-have. Server authority cannot be
  retrofitted into a shipped single-player codebase without rewriting the
  simulation's ownership model, so it is built from the start even if nothing
  ships on it.
- The public multiplayer **product** is Should-have, decided at the gate in
  [09 — Roadmap](09-roadmap.md).

Multiplayer code must never block campaign execution. That is a hard
constraint on how the networking gem is integrated, not a scheduling
preference.

## Performance scope

| Class | Target |
| --- | --- |
| Must-have | stable 60 FPS on the defined reference hardware; no critical streaming stutter in campaign levels; no reproducible shader hitches in release scenarios; defined Low/Medium/High presets |
| Should-have | 120 FPS on strong hardware; stable MP performance; 16–32 players within the server budget |
| Post-Launch | 50-player optimisation, further hardware classes, experimental high-end features |

See [07 — Budgets](07-budgets.md) for what is decided versus still open.

## Error severity

Release decisions use a fixed severity scale rather than per-bug argument:

| Class | Definition | Effect |
| --- | --- | --- |
| **S0** | crash, data loss, exploit, server outage, security breach, unrecoverable match or save state | **blocks release and deployment** |
| **S1** | severe gameplay fault, critical network or performance regression, non-reproducible save problems, loss of progression, blocked core player flow | **blocks release** |
| **S2** | significant fault with a workaround or limited scope | release requires a documented decision from QA, Engineering and Production |
| **S3** | limited fault without material effect on core flows | may be fixed after release |
| **S4** | cosmetic or purely internal | backlog |

## Why this chapter exists

Earlier revisions of the brief described campaign, 50-player multiplayer,
multiple platforms and live operations as one concurrent production. That
scope is not deliverable as a single launch, and the failure mode is not an
honest miss — it is that every system arrives at 80 % and nothing is
finishable. Classifying each feature once, and demoting automatically on the
second missed milestone, is what keeps that from being rediscovered at Beta.
