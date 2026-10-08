# ADR-0008 Rendering Extension Policy

Status: accepted
Owner: Rendering

## Context

The original draft specified a single AZSL shader performing fog, blur, ACES
tonemapping, film grain and letterboxing together, and more broadly implied
building substantial custom rendering inside O3DE.

Atom is already a modular, pass-driven and data-driven renderer, and RPI exists
specifically so a project can add its own passes and features.

## Problem

A monolithic post-processing shader cannot be reordered, cannot be budgeted per
effect, cannot be disabled per platform or quality tier, and cannot be profiled
to attribute cost to an individual effect. Each of those is a requirement
elsewhere in the TDD: GPU budgets per pass group, quality tiers, and automated
frame-time regression with per-pass attribution.

## Decision

Phoenix extends Atom through RPI render passes and does not build a parallel
renderer. Post-processing decomposes into discrete passes, each with an owner,
a GPU budget entry and a quality-tier rule; the hierarchy is in
`docs/tdd/05-rendering.md`.

Custom rendering follows an escalation ladder, each rung requiring more
justification than the last:

```
existing Atom feature -> configuration -> material/shader -> pass configuration
-> custom RPI pass -> engine extension -> engine fork
```

Rungs 1–4 need no architectural approval. A custom RPI pass needs a named
owner and a budget entry. An engine extension or fork needs an ADR.

Two pass-ordering constraints are load-bearing and recorded as such: film
grain must follow tonemapping, and UI must composite after tonemapping.

## Consequences

- Each effect is individually measurable, disableable and tier-gated.
- Shader variants become a budgeted, CI-monitored quantity rather than an
  emergent one.
- Rendering history may never determine gameplay correctness; temporal passes
  declare motion vectors as an explicit dependency rather than relying on a
  side effect.
