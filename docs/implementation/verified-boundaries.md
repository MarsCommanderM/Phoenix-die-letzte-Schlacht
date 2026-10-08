# Verified O3DE Boundaries

The repository is intentionally limited to APIs verified against O3DE
documentation and source:

- `project.json` `external_subdirectories`
- Gem manifest fields
- Multiplayer AutoComponents and `NetworkInput`
- `SaveDataSystemComponent`
- O3DE CMake/CLI gem activation model

Generated AutoComponent C++ is not committed. The repository does not claim
that every Phoenix class is an O3DE class; see `interfaces.md` for the
Phoenix-API versus O3DE-API split.

## Verified against O3DE tag `2605.0`

Checked by reading the engine source at the release tag — all 117
`Gems/**/gem.json` manifests, `Gems/RecastNavigation` as a reference gem, and
`Templates/DefaultGem`.

### Engine gem names

| Declared | Verdict | Action taken |
| --- | --- | --- |
| `Atom` | **exists** (`Gems/Atom`) | kept |
| `EMotionFX` | exists | kept |
| `Multiplayer` | exists | kept |
| `AudioSystem` | exists | kept |
| `LyShine` | exists | kept |
| `PhysX` | exists, **but it is the PhysX 4 gem** (`Gems/PhysX/Core/PhysX4`) | changed to **`PhysX5`** (`Gems/PhysX/Core/PhysX5`) |
| `Navigation` | **does not exist** | changed to **`RecastNavigation`** |
| `Prefab` | **does not exist** as a gem | **dropped.** `Gems/Prefab/PrefabBuilder` is a tools-time asset builder; runtime prefab and spawnable support lives in AzFramework, which every target already links |

The `PhysX` entry mattered most: the TDD pins **PhysX 5**, and declaring
`PhysX` would have silently delivered PhysX 4. Nothing would have reported the
mismatch — the gem exists, so activation would have succeeded.

An earlier revision of this file claimed `Atom` was suspect "because O3DE
ships the renderer as several `Atom_*` gems". That was wrong. Those gems do
exist (`Atom_RPI`, `Atom_RHI_Vulkan`, `Atom_Feature_Common`, and others), but a
gem named exactly `Atom` exists as well, and it is the correct aggregate
dependency.

### Gem build structure

The gem CMake was rewritten against `Gems/RecastNavigation`. Four differences
from the previous, memory-written version would each have failed at configure
time:

1. The gem root must call `o3de_gem_setup("<Gem>")`, which establishes
   `gem_name`, `gem_path`, `gem_restricted_path` and
   `gem_parent_relative_path`.
2. `o3de_pal_dir` takes **five** arguments, not two.
3. A gem declares **three** targets, not two: `<Gem>.API` (INTERFACE),
   `<Gem>.Private.Object` (STATIC, marked `O3DE_PRIVATE_TARGET TRUE`) and
   `<Gem>` (the module). Six aliases follow, including `.API` variants.
4. Platform files are `PAL_<platform>.cmake` for traits, plus a
   `<gemlower>_<kind>_files.cmake` list per kind, referenced as
   `${pal_dir}/<list>`.

The `<gemlower>_{api,private,shared}_files.cmake` naming was already correct
and matches the engine exactly.

### Engine gem target shapes differ

Engine gems do not all expose the same CMake targets. Checked at `2605.0`:

| Gem | Targets it exposes |
| --- | --- |
| `RecastNavigation` | `.API` (INTERFACE), `.Private.Object`, module, `.Clients/.Servers/.Unified` + `.API` aliases |
| `SaveData` | `.Static`, module, `.Clients` alias — **no `.API` target** |

So a Phoenix gem linking an engine gem must use that gem's actual target name.
`PhoenixCore` depends on `Gem::SaveData.Static`, not `Gem::SaveData.API`.
Assuming `.API` for every engine gem would fail at link time, which is why
each is looked up rather than inferred.

Phoenix's own gems all expose `.API`, so inter-gem dependencies use it
uniformly; that uniformity does not extend to the engine.

`SaveData` was missing from the manifests entirely until this check, even
though ADR-0004 builds the save architecture on it. `SceneProcessing` is
deliberately **not** declared as a gem dependency: it is asset-processing
infrastructure enabled at the project level with `o3de enable-gem`, not a
runtime dependency of any gameplay gem.

### Settings registry root

Both roots are in active use at `2605.0`, so the previous claim that `Amazon`
is simply "the legacy Lumberyard root" was too strong:

| Root | Example in the engine |
| --- | --- |
| `Amazon` | `Registry/prefab.editor.setreg`, `Registry/prefab.tools.setreg` |
| `O3DE` | `Registry/quality.setreg` |

`Amazon` persists for tools and editor settings; `O3DE` is used for newer
engine settings. Neither is correct for a *project's own* settings, which
should sit under a project-owned root. Phoenix feature flags therefore use
`/Phoenix/FeatureFlags/`.

**Still open:** whether `project/Registry/phoenix.settings.setreg` should keep
its `Amazon` root. It is a project settings file, so a `Phoenix` root is more
consistent with the above — but changing it affects anything already reading
those keys. Owner: Engineering. Target: M1.

### Collision layer fallback

`AzPhysics::CollisionLayers::GetLayer(name)` returns
`CollisionLayer::Default` — index 0 — when the name is not found, and the
`CollisionLayer(const AZStd::string&)` constructor routes through it. Read in
`Code/Framework/AzFramework/AzFramework/Physics/Collision/CollisionLayers.h`
and `.cpp` at tag `2605.0`; the engine's own doc comment states the fallback
explicitly. `CollisionLayers::MaxCollisionLayers` is 64.

Consequence: a misspelled collision layer name in data is not an error at
runtime. It silently assigns layer 0. This is the whole reason
`project/Config/Physics/layers.json` reserves index 0 as an inert `Default`
and why `tools/validation/validate_registries.py` enforces it — a collider
that falls through the world gets reported; one that collides with everything
looks almost right. See [TDD chapter 90](../tdd/90-source-reconciliation.md)
C15.

## Claims corrected after the fact

This section exists because a wrong claim that nobody revisits is worse than
no claim: it reads as verification. Two entries above were already corrected
this way (`Atom`, and the settings-registry roots). One more belongs here, and
it is about this repository's own history rather than the engine.

**The commit message for `040e572` is wrong.** It states that the two gates it
added, `scripts/check_architecture.py` and
`tools/validation/validate_versions.py`, "were adversarially reviewed for
vacuousness specifically". They were not. The review step that was supposed to
do it did not complete, and the message was written as though it had. The
commit is pushed, so it cannot be amended without rewriting a branch that is
already under review; the correction lives here instead.

What is true now, and checkable rather than asserted:

- `tests/Unit/test_architecture.py` carries negative tests for every rule the
  gate implements — direct, indirect and self cycles; a cycle reported once
  rather than once per member; four distinct ways of spelling a route into
  another gem's source tree; an unlisted AutoComponent XML; a declared path
  that does not exist; an uncovered `CODEOWNERS` area; a pattern with no
  owner; a catch-all that warns instead of passing silently.
- `tests/Unit/test_versions.py` does the same for the version contracts,
  including the one failure mode a grepping check would miss: a constant that
  is **commented out** in `PhoenixVersion.h` but still matches the regex. The
  parser strips comments, and the test proves it.

The standard this repository set for itself in ADR-0011 applies to review as
much as to hashes: a recorded verification that cannot be checked against what
was actually done is worse than none, because it looks like verification.

## Not verified

These need a registered engine or an owner's decision.

- **AutoComponent attribute sets.** The `NetworkProperty` attributes
  (`ReplicateFrom`, `ReplicateTo`, `Container`) in
  `project/Code/Source/AutoGen/*.AutoComponent.xml` follow the documented
  AutoComponent model but were not validated against the engine's
  AutoComponent schema. First action on a registered engine: run the generator
  and fix whatever the schema rejects. See `multiplayer-components.md`.
- **Whether `Atom` alone is sufficient** for the rendering integration, or
  whether `CommonFeaturesAtom` / `AtomLyIntegration` are also required. The
  gem exists and is the right aggregate; what a project needs beyond it
  depends on which features are used.
- ~~`LICENSE` versus the gem manifests.~~ **Resolved.** The project owner chose
  Apache-2.0; see [ADR-0011](../adr/0011-project-licence.md). `LICENSE` now
  holds the verbatim Apache-2.0 text and the manifests already matched. One
  item remains: the attribution line in `NOTICE` reads "the Phoenix authors",
  which is not a legal entity and must name a person or company before
  distribution.
