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
- **`LICENSE` versus the gem manifests.** Every `gems/*/gem.json` declares
  `"license": "Apache-2.0"`, while `LICENSE` is still a placeholder asking for
  the project's approved licence. These disagree. Choosing the project licence
  is a decision for the project owner, so neither side was changed; resolve it
  before any distribution.
