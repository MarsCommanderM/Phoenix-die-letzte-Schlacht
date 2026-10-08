# EP-NNNN Short title

Status: proposed
Owner: Name or role that rebases this patch
ADR: ../adr/NNNN-slug.md
Engine version: 26.05.0
Category: engine-bug
Upstream issue: https://github.com/o3de/o3de/issues/NNNN
Dropped in: n/a

## What the patch changes

The engine files touched, and what the change does. A diff summary, not the
diff: the diff lives in the fork.

## Why this cannot live in a Phoenix gem

ADR-0009 rule 2: anything achievable through a gem, an RPI pass, a component
or a data asset is not an engine patch. State what was tried and why it does
not reach.

## Rebase cost

What breaks when the engine moves, and roughly how much work a rebase is.
This is the number that makes the patch set's cost visible before upgrade
time rather than during it.

## Exit condition

What makes this patch unnecessary — an upstream fix shipping, an extension
point landing, a requirement being withdrawn. A patch with no exit condition
is a permanent fork of that file, and must say so here explicitly.
