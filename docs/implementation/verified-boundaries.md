# Verified O3DE Boundaries

The repository is intentionally limited to APIs verified against O3DE
documentation:

- `project.json` `external_subdirectories`
- Gem manifest fields
- Multiplayer AutoComponents and `NetworkInput`
- `SaveDataSystemComponent`
- O3DE CMake/CLI Gem activation model

Generated AutoComponent C++ is not committed. The repository does not claim
that every Phoenix class is an O3DE class.

## Not verified in this repository

These values were carried over from the initial starter and have **not** been
checked against an O3DE 26.05.0 installation. Confirm them against the
engine you register before relying on them.

- **Engine gem names in `gems/*/gem.json` `dependencies`.** The entries
  `PhysX`, `EMotionFX`, `Multiplayer`, `Atom`, `LyShine`, `AudioSystem`,
  `Navigation` and `Prefab` are treated as opaque strings by
  `scripts/validate.py`, which tier-checks only Phoenix-internal
  dependencies. A name that does not match a real gem will fail at
  `o3de enable-gem`, not here. `Atom` and `Navigation` in particular are
  suspect: O3DE ships the renderer as several `Atom_*` gems, and navigation
  support under other gem names.
- **The settings registry root in `project/Registry/phoenix.settings.setreg`.**
  It nests settings under `Amazon`, which is the legacy Lumberyard root.
  Newer O3DE settings commonly live under `O3DE`. Verify which root the
  pinned engine reads before adding settings that must take effect.
- **AutoComponent attribute sets.** The `NetworkProperty` attributes
  (`ReplicateFrom`, `ReplicateTo`, `Container`) in
  `project/Code/Source/AutoGen/*.AutoComponent.xml` follow the documented
  AutoComponent model but have not been validated against the engine's
  AutoComponent schema. First action on a registered engine: run the generator
  and fix whatever the schema rejects. See
  `multiplayer-components.md`.
- **`LICENSE` versus the gem manifests.** Every `gems/*/gem.json` declares
  `"license": "Apache-2.0"`, while `LICENSE` is still a placeholder asking
  for the project's approved license. These disagree. Choosing the project
  license is a decision for the project owner, so neither side was changed;
  resolve it before any distribution.
