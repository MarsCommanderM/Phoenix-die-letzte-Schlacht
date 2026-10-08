# Next Session: Phase 0 on a Machine With O3DE

Everything checked so far was checked without an engine.
`scripts/check_cmake.py` configures all 18 `CMakeLists.txt` against *stubs* of
the verified engine API, which shows the build structure is well formed — not
that the game builds. This is the runbook for the session that closes that
gap, written for **Lightning AI Studio** as the target but useful on any Linux
box with O3DE.

Run `python3 scripts/bringup.py --probe-only` first. It touches nothing and
tells you which of the points below apply to the machine you actually have.

## The three things that waste a day if you get them wrong

### 1. Build inside the persistent path

A hosted studio keeps one path and discards the rest when the instance stops.
On Lightning that path is under `/teamspace`; the home directory and `/tmp`
are not it. Clone the engine and this repository **inside** the persistent
root, or the multi-hour engine build has to be done again next time.

`bringup.py --probe-only` reports the persistent root it found and whether
this repository and the engine are inside it. If it reports finding none,
stop and confirm where the machine keeps data before building anything.

### 2. Compile on CPU, attach the GPU later

Building O3DE is CPU, RAM and disk work. A T4 contributes nothing to it. On a
platform that bills GPU time and lets the compute be switched, do the build on
the cheapest machine with the most cores, and attach the GPU only when
something needs to render.

The probe reports an attached GPU as a **warning** for exactly this reason.

### 3. Enable the gems before configuring

`project/Code/enabled_gems.cmake` is a comment and nothing else — it is an
O3DE-managed file this repository deliberately does not hand-maintain. The
consequence matters: **`cmake` run before `o3de enable-gem` succeeds** and
produces a project with no Phoenix code in it. That looks like progress.

`bringup.py` enables all eight Phoenix gems before configuring, then reads
`enabled_gems.cmake` back to check the step did what it reported. The eight
engine gems (`Atom`, `AudioSystem`, `EMotionFX`, `LyShine`, `Multiplayer`,
`PhysX5`, `RecastNavigation`, `SaveData`) arrive transitively through each
`gem.json`, so they are not enabled individually.

## Order of work

| # | Step | Command |
| --- | --- | --- |
| 1 | Probe the machine | `python3 scripts/bringup.py --probe-only` |
| 2 | Clone O3DE at the pinned tag, inside the persistent root | `git clone --branch 2605.0 https://github.com/o3de/o3de.git` |
| 3 | Bootstrap the engine's own dependencies | per O3DE's Linux setup docs for that tag |
| 4 | Review the plan without running it | `python3 scripts/bringup.py --engine <path> --dry-run` |
| 5 | Register, enable, configure | `python3 scripts/bringup.py --engine <path>` |
| 6 | Send `build/bringup-report.md` back | — |

Step 3 is the one this repository cannot help with: the engine's own
prerequisites (3rdParty packages, compiler and system libraries) are O3DE's
documentation to state, and they change between releases. Do not take them
from memory, including mine.

The engine tag is `2605.0`, **not** `26.05.0`. The project pins
`o3de==26.05.0` in `project/project.json`, which is the engine *version*; the
git tag spells it differently. Getting this wrong produces a
`compatible_engines` rejection, which `bringup.py` diagnoses by name.

## What success looks like, and what it does not

Phase 0 is done when `cmake --preset linux-server` configures against the real
engine with the eight Phoenix gems enabled. That is **configure**, not
compile, and not run.

On a headless machine that is also the natural stopping point: the O3DE Editor
needs a display and will not start, while the dedicated server and the Asset
Processor do not. `linux-server` is the only Linux preset in
`CMakePresets.json`, and on a headless box it is the right one.

## Expect the first run to fail

`bringup.py` has never been executed against an engine, because there is none
in the environment it was written in. Its probe, verdict rules, command
shapes, failure diagnosis and report writer are covered by 48 tests in
`tests/Unit/test_bringup.py`; the steps that invoke the O3DE CLI are not.

It is built to fail usefully rather than to look confident: every step prints
its command and why it exists, checks its own precondition, stops at the first
failure rather than cascading, and prints the engine's own stderr verbatim
next to the most likely cause. Unknown output gets *no* guessed cause — a
confident wrong diagnosis sends the next hour in the wrong direction.

Everything it learns goes to `build/bringup-report.md`. That file is the
deliverable of the session: it carries the machine's facts, every command, and
every failure's exact output.

## What this unblocks

| Blocked today | Needs |
| --- | --- |
| The first real build | this runbook |
| AutoComponent `NetworkProperty` attributes (`verified-boundaries.md`) | the generator, which needs a configured project |
| `.clang-tidy` as a CI gate ([ADR-0012](../adr/0012-cpp-tooling.md)) | `compile_commands.json`, which cmake emits once configured |
| All 81 `null` budget values ([07](../tdd/07-budgets.md)) | a build to measure, on named reference hardware |

See [chapter 09](../tdd/09-roadmap.md) for where Phase 0 sits in the sequence.
