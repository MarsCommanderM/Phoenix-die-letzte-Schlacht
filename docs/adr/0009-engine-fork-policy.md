# ADR-0009 Engine Fork Policy

Status: accepted
Owner: Engineering

## Context

Phoenix runs on a controlled O3DE 26.05.0 fork. The engine is pinned exactly
so that builds reproduce from a commit, which acceptance criterion 1 requires.

## Problem

The cost of a fork is not the initial patch. It is every subsequent engine
upgrade multiplied by the number of carried patches. Left unmanaged, the patch
set grows quietly and the cost appears only at upgrade time, when it is too
late to choose differently.

## Decision

O3DE is patched only for demonstrably engine-wide requirements:

- an engine bug
- a required extension point
- a measured performance requirement
- a platform requirement
- a security fix

Explicitly **not** for: a gameplay shortcut, designer convenience, a
mission-specific feature, or a temporary prototype.

Rules:

1. Every patch requires an ADR naming the upstream issue, why the change
   cannot live in a Phoenix gem, and the engineer who owns rebasing it.
2. Anything achievable through a gem, an RPI pass, a component or a data asset
   is not an engine patch.
3. The patch set is reviewed at every engine upgrade; a patch whose upstream
   issue is fixed is dropped rather than carried.
4. The fork never diverges in file formats, asset schemas or serialisation
   identity without an ADR, because those changes are not reversible once
   content exists.
5. No engine upgrade lands directly on the production branch.

## Consequences

- The patch set is a tracked liability with visible cost rather than a
  discovery at upgrade time.
- Rule 4 is the strictest, because serialisation divergence cannot be undone
  after content has been authored against it.
- Engine upgrades follow the sequence in `docs/tdd/01-engine-baseline.md`:
  branch, compile, asset processing, tests per domain, performance, QA, merge.
