# ADR-0011 Project Licence

Status: accepted
Owner: Project owner

## Context

The imported starter shipped a `LICENSE` placeholder reading "Replace this
placeholder with the project's approved license before distribution", while
all eight `gems/*/gem.json` manifests declared `"license": "Apache-2.0"` with
the Apache licence URL.

Those disagreed, in a public repository. The manifests were almost certainly
generator boilerplate rather than a decision, so the repository was
simultaneously claiming a permissive open-source licence and stating that no
licence had been chosen.

## Problem

A licence is not a technical default that can be left to settle. Until one is
chosen, nobody — including contributors — knows what they may do with the
code, and the contradiction above meant the repository gave two different
answers.

## Alternatives

1. **Apache-2.0.** Permissive open source. Anyone may use, modify and
   distribute the code, including in a commercial product that competes with
   Phoenix, provided they preserve the notice and state changes. Grants a
   patent licence. No fees.
2. **Proprietary / all rights reserved.** The code stays with the copyright
   holder. Nobody may redistribute it. Also no fees.
3. **Copyleft (GPL family).** Derivatives must be released under the same
   terms. Generally incompatible with shipping a closed commercial game and
   with some platform distribution agreements.

## Decision

**Apache-2.0**, chosen by the project owner.

The licence text in `LICENSE` is a verbatim copy of `LICENSE_APACHE2.TXT` from
the O3DE source tree at tag `2605.0`, taken from that source rather than
retyped so the text cannot carry a transcription error.

The upstream file uses CRLF line endings and `.gitattributes` normalises text
to LF, so the committed file differs from upstream in line endings only — the
201 lines are byte-identical after normalisation. Both hashes are recorded in
`NOTICE` so the committed file stays independently verifiable:

    sha256sum LICENSE  ->  7382b1cf711e7a7c7af9816e0e07b49b91e7149b7c6d347225f98800fcb1f1c2

An earlier revision of this ADR cited only the upstream CRLF hash, which does
not match the file in the repository. A recorded hash that cannot be checked
against what is committed is worse than none, because it looks like
verification. The gem manifests already matched, so no manifest changed.

`NOTICE` carries the copyright attribution, the SPDX identifier, and the
third-party notices.

## Consequences

- The eight gem manifests and `LICENSE` now agree. The contradiction is gone.
- **The source is open.** Anyone may fork Phoenix, modify it, and ship a
  commercial product built on it, as long as they preserve the notice and
  state their changes. This is the substantive effect of the choice and is
  recorded here because it is easy to read "no fees" as "no consequences".
  The decision was made with that effect stated.
- Apache-2.0 is compatible with O3DE, which is itself Apache-2.0 OR MIT, so
  the engine imposes no conflict.
- **The copyright holder is Michael Braunschweig**, named by the project owner
  and recorded in `NOTICE`. Section 4(d) of the licence makes that line
  travel with every copy and every derivative work, so it is checked by
  `tests/Unit/test_documentation.py` rather than left to be noticed. A later
  assignment to a company changes the line going forward only: copies already
  distributed keep the name they were shipped with, which is why this was
  worth settling before the first release.
- Reversing this is possible for future versions but **not retroactive**:
  anyone who received a copy under Apache-2.0 keeps those rights for that
  copy. If the intent was to keep the code private, that decision is cheapest
  now and gets more expensive with every push.
- Per the repository contract, a licence change needs elevated review; see
  `CONTRIBUTING.md`.
