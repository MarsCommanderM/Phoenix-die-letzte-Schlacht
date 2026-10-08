# Asset Naming

Master Baseline v5.1 §231 requires a single asset naming convention. This is
it, together with what enforces it:
`tools/validation/validate_asset_naming.py`, which runs in CI on every pull
request.

## Why a convention needs a validator

A naming convention written down and not enforced lasts about three weeks.
The failure is not aesthetic. O3DE resolves assets by path, and asset paths
are **case-sensitive on Linux and case-insensitive on Windows**. A texture
referenced as `T_Rock_BC.png` and stored as `t_rock_bc.png` loads on a
developer's Windows machine and fails on the dedicated Linux server build,
which is the single worst place to discover it: the machine nobody is
watching, after the change has already been reviewed and merged.

The second reason is search. A flat prefix tells you what a file is before
you open it, and makes `T_*` a complete answer to "every texture", which an
asset audit needs and a mixed convention cannot give.

## Rules

### Identifiers and data documents

Gameplay data is `lower_snake_case`, both the filename and the `id` inside.

A document under `project/Assets/Data/<Category>/` is named
`<singular-category>_<name>.json`:

| Category | File | Id |
| --- | --- | --- |
| `Actions` | `action_interact.json` | `action_interact` |
| `Missions` | `mission_intro.json` | `mission_intro` |
| `Objectives` | `objective_reach_exit.json` | `objective_reach_exit` |

The prefix is redundant with the directory and that is the point: an id is
quoted in bug reports, logs and save files far from its directory, and
`intro` alone does not say what it is.

Agreement between a document's `id` and its filename is enforced separately,
by `tools/validation/validate_assets.py`.

Schemas are `<name>.schema.json`, in `project/Assets/Schema/` for authoring
data and `project/Config/Schema/` for configuration.

### Production assets

Produced assets are `PascalCase` with a type prefix. These are the file kinds
the pipeline will carry; none are authored yet, and the validator reports
that fact rather than passing silently over an empty tree.

| Prefix | Kind | Extensions | Example |
| --- | --- | --- | --- |
| `T_` | Texture | `.png`, `.tga`, `.tif`, `.exr` | `T_RockCliff_BaseColor.png` |
| `M_` | Material | `.material` | `M_RockCliff.material` |
| `SM_` | Static mesh | `.fbx` | `SM_RockCliff.fbx` |
| `SK_` | Skinned mesh | `.fbx` | `SK_CharacterBase.fbx` |
| `A_` | Animation | `.fbx`, `.motion` | `A_CharacterRun.fbx` |
| `P_` | Prefab | `.prefab` | `P_SupplyCrate.prefab` |
| `S_` | Sound | `.wav`, `.ogg` | `S_FootstepMetal.wav` |
| `L_` | Level | `.prefab` under `Levels/` | `L_TrainingGround.prefab` |

Texture suffixes name the channel, so a packed texture is identifiable
without opening it: `_BaseColor`, `_Normal`, `_Roughness`, `_Metallic`,
`_AO`, `_Emissive`, `_ORM` (occlusion/roughness/metallic packed).

### Rules that apply to every path

- ASCII letters, digits, `_`, `.` and `/` only. No spaces, no accented
  characters. A space in an asset path survives the editor and breaks command
  lines, `.setreg` entries and shader include paths.
- No two files in the repository may differ only by case. This is the Linux
  server failure above, and it is checked across the whole tree, not only
  under `Assets/`.
- No trailing version or status in a name: not `_final`, `_v2`, `_new`,
  `_old`, `_copy`, `_wip`, `_temp`, `_bak`, `_test`. Version control is the
  version control. A `_final` in a filename is a promise the next commit
  breaks, and these names are how a tree accumulates files nobody dares
  delete.

## What is deliberately not enforced

- **Texture resolution and compression** belong to the asset processing
  settings, not the filename.
- **Per-feature sub-prefixes** (`T_UI_`, `T_Env_`) are not mandated. Directory
  structure already carries that, and two coordinates for the same fact drift
  apart.
- **C++ file names** are not covered here. Those follow the engine's own
  conventions; `.clang-format` and review carry that, per
  [ADR-0012](../adr/0012-cpp-tooling.md).

## Changing this document

A new prefix is added here *and* to `PRODUCTION_PREFIXES` in the validator in
the same change. `tests/Unit/test_asset_naming.py` compares the two and fails
if they disagree, so the table cannot drift away from what is enforced.
