# ADR-0006 Starter Corrections

Status: accepted

## Context

The repository was seeded from the `Phoenix_O3DE_26_05_0_Starter` archive.
The import commit preserves that archive unmodified. Reviewing it surfaced
defects that made the baseline non-functional rather than merely minimal:

1. All eight `gems/*/CMakeLists.txt` were unparseable. Each opened with
   `cmake_minimum_required(VERSION 3.22` and then listed header paths as
   trailing arguments, so the closing parenthesis terminated
   `cmake_minimum_required` instead of a file list. `cmake` rejects every one
   with "called with unknown argument".
2. `project/Code/Phoenix_files.cmake` declared 16 paths, 14 of which did not
   exist under `project/Code/`; they named files belonging to the gems. That
   also duplicated gem-owned code into the project target, contradicting the
   documented dependency direction.
3. No component was ever registered. Every system component was declared
   inside its own `.cpp`, so no module could name it, and every module left
   `m_descriptors` empty.
4. The four CI workflows lived in `ci/pipelines/`. GitHub only runs
   workflows from `.github/workflows/`, so none of them ever executed.
5. `scripts/test.py` collected zero tests, because `tests/Unit/` was not a
   package, and still exited 0 - the test gate passed without running the
   two tests that existed.
6. `scripts/package.py` excluded only `build/` and `packages/`, so the whole
   `.git` directory, including `.git/config`, was written into the release
   archive.
7. `PhoenixTypes.h` used `AZ::EntityId` without including its header.

## Decision

Correct all seven in a single follow-up commit, keeping the import commit
pristine so each correction is reviewable as a diff against the original.

Generate the CMake file lists from the tree rather than maintaining them by
hand, so a declared path cannot drift from a real one.

Make the gates enforce what the documentation claims: `scripts/validate.py`
checks asset data against its schema, resolves mission/objective references
and enforces the gem tiers; `scripts/check_cmake.py` configures every file
list with the real `cmake`; `scripts/test.py` fails when discovery collects
nothing.

Assign real UUIDs to the module and system component types. The placeholders
shared a common all-zero prefix, and nothing has been serialized against
them yet, so this is the cheapest possible moment to change them.

## Consequences

The baseline configures, registers its components and has a CI gate that can
fail. Values that could not be verified without a registered O3DE 26.05.0
engine are recorded in `docs/implementation/verified-boundaries.md` rather
than silently changed; notably the engine gem names, the settings registry
root, and the licence mismatch between `LICENSE` and the gem manifests.
