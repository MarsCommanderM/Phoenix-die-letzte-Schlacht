# Engine Patch Register

The operational half of [ADR-0009](../adr/0009-engine-fork-policy.md).

ADR-0009 sets the policy: O3DE is patched only for an engine bug, a required
extension point, a measured performance requirement, a platform requirement
or a security fix, and every patch needs an ADR, an owner and a review at
every engine upgrade. This directory is what makes rule 3 executable, because
"reviewed at every upgrade" needs a list to review.

## Carried patches

**None.** The fork is currently identical to O3DE `2605.0`.

| Patch | Title | Category | Owner | Engine version | Status |
| --- | --- | --- | --- | --- | --- |

The table is empty on purpose, and that is a stronger statement than an absent
file: it says the patch set was checked and is zero, where no register at all
says only that nobody wrote one down. `tools/validation/validate_engine_patches.py`
keeps the table and the files on disk in agreement, so a patch cannot be added
without appearing here, and a row cannot be left behind after its patch is
dropped.

## Why the register exists separately from the ADRs

An ADR records a decision at a point in time. The liability it creates is
ongoing, and the two need different shapes:

- The ADR answers *why we did this*, once, and does not change afterwards.
- The register answers *what are we carrying right now*, which is the question
  an engine upgrade asks, and which changes every time a patch lands or is
  dropped.

Keeping the second inside the first means reading eleven ADRs to answer a
question that should be one table. Worse, it means a dropped patch leaves its
ADR saying "we patch this", which is then wrong.

## Adding a patch

1. Write the ADR first. Without it there is no decision, only a change.
2. Copy `TEMPLATE.md` to `NNNN-slug.md`, next number, and fill every field.
   `Upstream issue` is required: either a link, or `none - <where it was
   reported>`. "Not reported" is not an option, because an unreported engine
   bug is a patch that can never be dropped.
3. Add the row to the table above.
4. Run `python3 tools/validation/validate_engine_patches.py`.

## Dropping a patch

A patch whose exit condition is met is dropped, not carried. Set
`Status: dropped` and fill `Dropped in:` with the engine version that made it
unnecessary, then remove its row from the table. The file stays: it is the
record of a cost that was paid and ended, and the next person proposing the
same patch should be able to find out what happened to the last one.

## Field reference

Every patch file declares these, and the validator requires each one:

| Field | Meaning |
| --- | --- |
| `Status` | `proposed`, `carried` or `dropped` |
| `Owner` | Who rebases it. ADR-0009 rule 1; a patch with no owner is rebased by whoever is unlucky |
| `ADR` | Relative path to the deciding ADR |
| `Engine version` | The engine version the patch was written against |
| `Category` | One of the five admissible reasons in ADR-0009 |
| `Upstream issue` | A link, or `none - <where reported>` |
| `Dropped in` | The engine version that ended it, or `n/a` |

And these sections: **What the patch changes**, **Why this cannot live in a
Phoenix gem**, **Rebase cost**, **Exit condition**.
