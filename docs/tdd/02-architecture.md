# 02 — Module Architecture and Dependency Rules

## Core rule

O3DE provides engine capabilities. Phoenix owns game rules.

Stated negatively: no Phoenix module re-implements a solver, a renderer, a
transport or an asset pipeline that the engine already ships.

## Gem tiers

Phoenix responsibilities live in eight small domain gems rather than one
mega-gem (ADR-0002). The gems form four tiers; a gem may depend on strictly
lower tiers only, and never within its own tier.

| Tier | Gems | May depend on |
| --- | --- | --- |
| 0 | `PhoenixCore` | O3DE only |
| 1 | `PhoenixGameplay` | tier 0 |
| 2 | `PhoenixCharacter`, `PhoenixWorld` | tiers 0–1 |
| 3 | `PhoenixAI`, `PhoenixNetworking`, `PhoenixPresentation`, `PhoenixTools` | tiers 0–2 |

```
PhoenixAI   PhoenixNetworking   PhoenixPresentation   PhoenixTools   (tier 3)
         \         |   \                |                   |
          \        |    \               |                   |
   PhoenixCharacter      PhoenixWorld                       |        (tier 2)
                  \            /                            /
                   PhoenixGameplay  <------------------------         (tier 1)
                          |
                    PhoenixCore                                       (tier 0)
                          |
                        O3DE
```

The tiers are enforced, not advisory. `scripts/validate.py` reads every
`gems/*/gem.json`, resolves Phoenix-internal dependencies against this table
and fails on any dependency that does not point strictly downward. It also
asserts that each gem's CMake `BUILD_DEPENDENCIES` agree with its manifest, so
the build graph and the declared graph cannot drift apart.

Engine gems (`PhysX`, `EMotionFX`, `Multiplayer`, Atom's gems, ...) are owned
by O3DE and are not tier-checked.

## Ownership

| Concern | Owner |
| --- | --- |
| Gameplay truth | Phoenix simulation |
| Presentation | Observes simulation; never a source of truth |
| Networking | Transports and synchronises simulation state |
| Save | Persists product state under a versioned schema |
| Physics solver | O3DE PhysX 5 |
| Render passes | Atom RPI, extended by `PhoenixPresentation` |

The asymmetry is deliberate: presentation reads simulation state and must
never write it. A visual system that can change gameplay truth is
indistinguishable from a desync in a server-authoritative game.

## Build target shape

Each gem produces three targets plus six aliases. This shape is taken from the
engine's own gems (`Gems/RecastNavigation` at tag `2605.0`), not invented:

| Target | Kind | Contents |
| --- | --- | --- |
| `<Gem>.API` | INTERFACE | the public headers dependent gems consume |
| `<Gem>.Private.Object` | STATIC | the implementation, marked `O3DE_PRIVATE_TARGET TRUE`; private to the gem's own CMakeLists |
| `<Gem>` | loadable module | the module entry point, linking `.API` publicly and `.Private.Object` privately |
| `<Gem>.{Clients,Servers,Unified}` | aliases | launcher-role resolution |
| `<Gem>.{Clients,Servers,Unified}.API` | aliases | the API target per launcher role |

Inter-gem dependencies are declared against `.API`, never against another
gem's private object library. That is what makes the tier table enforceable: a
gem can consume its dependency's headers and nothing else.

The gem root calls `o3de_gem_setup("<Gem>")`, which establishes `gem_name`,
`gem_path`, `gem_restricted_path` and `gem_parent_relative_path`; the Code
directory needs all four for `o3de_pal_dir` to resolve the platform folder.

File lists are split the way the engine expects:

| List | Contents |
| --- | --- |
| `<gem>_api_files.cmake` | public headers under `Code/Include/` |
| `<gem>_private_files.cmake` | implementation sources, excluding the module entry point |
| `<gem>_shared_files.cmake` | the module entry point |
| `Platform/<Platform>/PAL_<platform>.cmake` | platform traits (`PAL_TRAIT_*`) |
| `Platform/<Platform>/<gem>_<kind>_files.cmake` | platform-specific sources per kind, referenced as `${pal_dir}/<list>` |

A gem's system component is declared in a public header, registered through
the module's `m_descriptors`, and returned from
`GetRequiredSystemComponents()`. Both steps are required: the first makes the
component reflectable, the second makes it exist. A component declared only
inside its own translation unit is invisible to its module and can never be
created.

## Project module

The project owns only its own code. Every domain responsibility reaches it
through `project.json` `external_subdirectories`. `project/Code` therefore
lists exactly its own sources — the project target never restates gem files,
because doing so would both duplicate compilation and invert the dependency
direction above.

## Adding a gem

1. Create the gem with the target shape above.
2. Add it to `project.json` `external_subdirectories`.
3. Add it to `TIERS` in `scripts/validate.py` with its tier.
4. Add it to `EXPECTED_GEMS` in `tests/Unit/test_repository_contract.py`.
5. Enable it with `o3de enable-gem`; never hand-edit `enabled_gems.cmake`.

Validation fails until steps 2–4 agree with the tree, which is the point: a
new gem cannot enter the build without declaring where it sits in the graph.
