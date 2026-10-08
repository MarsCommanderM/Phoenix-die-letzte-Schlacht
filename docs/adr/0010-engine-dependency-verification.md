# ADR-0010 Engine Dependency Verification

Status: accepted
Owner: Engineering

## Context

The gem manifests inherited from the starter declared eight engine gem
dependencies: `Atom`, `EMotionFX`, `Multiplayer`, `AudioSystem`, `LyShine`,
`PhysX`, `Navigation` and `Prefab`. None had been checked against an engine.

An earlier revision of `verified-boundaries.md` flagged `Atom` and
`Navigation` as "suspect" from memory, which was half right and half wrong —
exactly the failure mode that makes unverified claims expensive.

## Problem

A wrong gem name fails at `o3de enable-gem`, which is late but loud. A gem
name that is *right but means something different* fails silently, which is
worse.

## Decision

Verify every engine dependency against the engine source at the pinned tag,
and record the result rather than an impression.

Verified at O3DE tag `2605.0` by reading all 117 `Gems/**/gem.json` manifests:

| Declared | Result |
| --- | --- |
| `Atom`, `EMotionFX`, `Multiplayer`, `AudioSystem`, `LyShine` | exist; kept |
| `PhysX` | exists, but is the **PhysX 4** gem → changed to `PhysX5` |
| `Navigation` | does not exist → `RecastNavigation` |
| `Prefab` | not a gem → dropped |

The `PhysX` finding is the consequential one. ADR-0001 and the TDD pin
**PhysX 5**; `Gems/PhysX/Core/PhysX4` is registered as `PhysX` and
`Gems/PhysX/Core/PhysX5` as `PhysX5`. Declaring `PhysX` would have activated
PhysX 4 successfully and silently, contradicting the stated baseline with
nothing to report the mismatch.

`Prefab` was dropped rather than renamed: `Gems/Prefab/PrefabBuilder` is a
tools-time asset builder, so a runtime gameplay gem depending on it would be
wrong. Runtime prefab and spawnable support lives in AzFramework, which every
target already links.

## Consequences

- The dependency names in `gems/*/gem.json` are now expected to succeed at
  `o3de enable-gem`, and to deliver the PhysX version the TDD specifies.
- The same verification pass corrected the gem build structure; see
  `verified-boundaries.md` for the four differences found against
  `Gems/RecastNavigation`.
- Engine dependencies are re-verified at every engine upgrade, as part of the
  patch-set review required by ADR-0009. A gem rename between releases is
  otherwise invisible until the build breaks.
