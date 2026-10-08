# ADR-0007 Launch Anchor and Player Scale

Status: accepted
Owner: Production / Engineering

## Context

Three source documents were supplied as the project brief and disagreed about
what the product commits to at launch:

- Master Baseline v5.2 §101 excludes "50+ Player Production" from MVP.
- MVP backlog 6A §6A.24 states multiplayer is not part of the minimal
  single-player MVP; §6A.26 ladders 1→32 and calls 50 a separate stretch gate.
- Architecture Baseline Rev 4.0 names the single-player campaign as the launch
  anchor, with public multiplayer only after a gate, and §48 states "50
  players is not a design argument, 50 players is a measurement target".

An earlier draft of the consolidated TDD nevertheless listed
"dedicated-server matches of up to 50 players" as a binding production goal.
That contradicted three of the four positions.

## Problem

A binding 50-player commitment and a gated single-player launch imply
different architectures, different budgets and a different roadmap. The
project cannot hold both.

## Alternatives

1. **Commit to 50 players at launch.** Rejected: no source supports it, and it
   would make acceptance criterion 2 a commitment rather than a measurement.
2. **Defer the multiplayer architecture entirely until after launch.**
   Rejected: server authority cannot be retrofitted into a shipped
   single-player codebase without rewriting the simulation's ownership model.
3. **Single-player launch anchor, multiplayer architecture from the start,
   public multiplayer behind a gate, player count as a measurement ladder.**

## Decision

Alternative 3.

The launch anchor is the single-player campaign. The multiplayer architecture
— server authority, replication model, protocol versioning, server validation
— is built from the start. Public multiplayer ships only after the gate in
`docs/tdd/08-quality-gates.md`.

Player count is a measurement ladder, not a commitment: 2 → 8 → 16 → 32, with
50 as a separate stretch gate. If 50 endangers product quality it moves
post-launch.

## Consequences

- Acceptance criterion 2 is phrased per ladder rung, and a rung is not claimed
  until measured.
- The authority rules in `docs/tdd/04-multiplayer.md` apply to single-player
  development too, which costs some discipline now and avoids a rewrite later.
- Deferring 50 players carries no architectural loss, which is the property
  that made alternative 3 acceptable.
