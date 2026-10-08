# 05 — Rendering and the Atom Pass Hierarchy

Owner: `PhoenixPresentation` (tier 3), extending Atom. Atom sits entirely
below the Phoenix gameplay layer.

```
Gameplay -> Presentation State -> Atom -> RPI -> RHI -> Vulkan -> GPU
```

Phoenix never renders through its own graphics API.

## Escalation ladder

Custom rendering is built only when the cheaper rung cannot do the job. Each
rung down carries a higher burden of justification:

```
1. Existing Atom feature
2. Configuration of that feature
3. Material / shader
4. Pass configuration
5. Custom RPI pass
6. Engine extension
7. Engine fork            <- requires an ADR
```

Rungs 1–4 need no architectural approval. Rung 5 needs a named owner and a
budget entry. Rungs 6–7 need an ADR.

## The monolithic shader is rejected

The original draft specified one AZSL shader performing fog, blur, ACES
tonemapping, grain and letterboxing together. That is rejected.

A single combined shader cannot be reordered, cannot be budgeted per effect,
cannot be disabled per platform or quality tier, and cannot be profiled to
attribute cost. Atom treats these as separate, reorderable passes precisely so
that each of those operations is possible. AZSL source and shader assets are
then processed by the existing shader build pipeline.

## Pass hierarchy

**Read this table as an ordering contract, not as a build list.** It states
which stages exist and in what order they must run. It does **not** commit
Phoenix to implementing each one as a custom RPI pass: most are Atom features
that are configured, not written. Which entries become custom Phoenix passes
is decided per entry, against the escalation ladder above.

A superseded revision of the brief named eight custom passes
(`PhoenixDepthPass`, `PhoenixVelocityPass`, `PhoenixTemporalPass`, and
others). A later revision explicitly withdrew that: a pass is not created
"just because the name looks good". Every custom pass needs five things
before it exists:

| Required | Why |
| --- | --- |
| Use case | a pass with no consumer is dead GPU time |
| Measured performance cost | it gets a line in the GPU budget or it is not approved |
| Alternative analysis | which Atom feature or material was tried first and why it was insufficient |
| Owner | per the rule that no system reaches production without one |
| Test | a render regression scene that would catch it breaking |

Each stage below carries an owner, a GPU budget entry and a quality-tier rule:

| # | Pass | Depends on | Disable-able | Notes |
| --- | --- | --- | --- | --- |
| 1 | Depth / prepass | — | no | Supplies depth for later passes |
| 2 | Forward / deferred opaque | 1 | no | Geometry and materials |
| 3 | Shadow resolve | 1 | tier-gated | Quality tiers S/A/B/C |
| 4 | Lighting | 2, 3 | no | |
| 5 | Transparency | 4 | no | |
| 6 | Volumetric fog | 1, 4 | yes | Own budget; first to drop on tier C |
| 7 | Motion vectors | 2 | no (if temporal on) | Required by any temporal pass |
| 8 | Depth of field / blur | 4, 7 | yes | Cinematic; separate from fog |
| 9 | Bloom | 4 | yes | |
| 10 | Tonemap (ACES) | 4, 6, 8, 9 | no | Colour pipeline anchor |
| 11 | Film grain | 10 | yes | After tonemap, deliberately |
| 12 | Letterbox / framing | 11 | yes | Cinematic framing only |
| 13 | UI composite | 10 | no | LyShine; never part of the graded image |

Two ordering constraints are load-bearing: grain must come **after** tonemap
or it is graded along with the image, and UI must composite **after** tonemap
or the HUD is tonemapped with the scene.

Each pass declares inputs, outputs, attachments and connections through RPI's
pass interfaces; the pass system manages them.

## Temporal rendering

Temporal features may require motion vectors, history buffers, reprojection
and disocclusion handling.

**Hard rule:** rendering history never determines gameplay correctness. A
temporal artefact may look wrong; it may never make a shot register
differently. This is why pass 7 exists as an explicit dependency rather than
an implicit side effect.

## Materials

Only material classes with an actual use case:

`PBR`, `Glass`, `Water`, `Foliage`, `Skin`, `Cloth`, `Decal`, `VFX`.

No material class is created speculatively. There is no global mega-shader
file; shaders are organised in families matching the list above.

## Shader variants

Every variant costs build time, memory, disk, runtime selection complexity and
QA surface. Variants are therefore gated:

```
Variant requested -> Is it required?
                     |- no  -> reject
                     +- yes -> measure -> approve
```

CI monitors the variant count against the budget in [07](07-budgets.md). An
unbounded permutation matrix is a release blocker, not a tuning issue.

## Animation LOD

Quality tiers, so that fidelity is spent where it is visible:

| Tier | Update rate | IK | Additives | Facial |
| --- | --- | --- | --- | --- |
| Hero | full | full | full | yes |
| Gameplay | full | reduced | reduced | no |
| Background | reduced | none | none | no |
| Dormant | none | none | none | no |

The goal is not maximum quality everywhere; it is maximum quality where it is
seen.
