# ADR-0012 C++ Tooling

Status: accepted
Owner: Engineering

## Context

Master Baseline v5.1 §150 requires `.clang-format` and `.clang-tidy` at the
repository root. Neither existed. The 65 committed C++ files were written in
something close to O3DE house style, but "close to" is not a contract: the
tree had three systematic divergences from the engine's published style and
nothing that would have caught a fourth.

## Problem

Both files are easy to ship and easy to have lie to you.

A `.clang-format` the tree already violates is not a style. It is a pending
60-file diff attached to whichever unlucky change first runs the formatter,
and it makes every later diff unreadable by mixing reformatting into it.

A `.clang-tidy` naming a check that clang does not have is worse, because
clang-tidy does not error on an unknown check — it ignores it. The file reads
as a 65-check gate while enforcing 64, or, if the list is wrong enough, none.
Nothing fails; the coverage is simply imaginary.

## Alternatives

1. **Write a config that matches the code as it stands.** Rejected. It means
   inventing a house style nobody shares, encoding accidents of how the files
   happened to be typed, and permanently diverging from the engine every
   contributor's editor is already set up for.
2. **Ship the config and leave the tree unformatted**, to be fixed "later".
   Rejected: this is precisely the vacuous gate the quality chapter forbids.
   A rule the codebase violates on day one teaches that the rules are
   decorative.
3. **Adopt the engine's config and reformat the tree to it.** Chosen.
4. **Enable `clang-tidy` broadly** (`bugprone-*`, `cppcoreguidelines-*`,
   `readability-*`). Rejected: against an O3DE codebase these fire constantly
   on correct code — `AZ::SystemAllocator`, `AZStd` containers and intrusive
   component lifetimes all violate the core guidelines by design. A gate that
   cries wolf gets suppressed wholesale, and a suppressed gate catches
   nothing.

## Decision

**`.clang-format` is the engine's own file, copied verbatim** from O3DE tag
`2605.0`, sha256
`4857426bd80a3d4ff6847d05e597f193c0cad839a7890de4f32782f6ff9795ab`. The hash
is checked against the committed bytes by
`tests/Unit/test_cpp_tooling.py`, so it is a hash that can actually be
verified rather than one that merely looks like verification.

The 65 sources were reformatted to conform. The diff is mechanical and falls
into three classes, all of them movements toward the engine's style:

| Change | Cause |
| --- | --- |
| `}` → `} // namespace Phoenix` | `FixNamespaceComments: true` |
| inheritance joined onto the class line | `BreakInheritanceList: BeforeComma` at `ColumnLimit: 140` |
| single-line `enum class` expanded | `BreakBeforeBraces: Custom`, `AfterEnum: true` |

One site is exempted with `// clang-format off`: the `AllFlags[]` array in
`PhoenixFeatureFlags.cpp`, which must list every enumerator. One flag per line
makes adding one a one-line diff a reviewer cannot miss; column-packed, the
same change reflows the whole block and hides in the noise. The exemption
carries that reason inline.

**`.clang-tidy` is Phoenix's own** — the engine ships none — and is narrow by
construction: 65 checks, each named individually, no wildcards. The admission
rule is that a check belongs only if, when it fires on this codebase, a
reviewer would also call the result a defect. Every excluded family is
excluded *in the file with its reason written down*, so the next person
arguing for `cppcoreguidelines-*` is arguing with a position rather than with
silence. `WarningsAsErrors: '*'` follows from the narrowness: a warning nobody
must fix is a warning nobody fixes.

## Consequences

- `clang-format --dry-run -Werror` over the tree is clean, and
  `tests/Unit/test_cpp_tooling.py` keeps it clean, with a negative test that
  proves the check can still fail.
- Every name in `.clang-tidy` is compared against `clang-tidy --list-checks`
  in both directions, so a typo that would silently disable a check fails the
  suite instead.
- **`.clang-tidy` is not yet a CI gate.** It needs `compile_commands.json`,
  which O3DE generates only when the project is configured against a
  registered engine — which this repository cannot do on its own. This is
  stated in the file itself rather than left to be discovered. It becomes a
  gate at the milestone that produces a build machine; see
  `docs/tdd/08-quality-gates.md`.
- Diverging from the engine's format later is permitted but is an amendment to
  this ADR: the file and the recorded hash change together, so the divergence
  is visible in review instead of arriving as drift.
