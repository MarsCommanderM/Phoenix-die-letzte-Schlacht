# Phoenix — Technical Design Document v1.0

Status: **v1.0 — accepted as the shared technical reference**
Engine baseline: O3DE 26.05.0
Owner of this document: Engineering

This is the common technical reference for Engineering, Gameplay, Art, Audio,
QA, Online and Production.

It consolidates three source documents (Master Baseline v5.2, the 6A MVP
backlog, and Architecture Baseline Revision 4.0) which contradicted each other
in six places — launch anchor and player scale, gem count, tools dependencies,
ADR numbering, file-list naming, and server tick rate. Each conflict is
resolved once, with its reason, in
[90 — Source Reconciliation](90-source-reconciliation.md). Reading that chapter
first is worthwhile if you remember a decision differently from how it is
stated here. Where a discipline needs a decision, this document
is where that decision lives; where a decision is still open, it is marked
**OPEN** with a named owner rather than left implicit.

## Contents

| # | Chapter | Primary audience |
| --- | --- | --- |
| [00](00-executive-summary.md) | Executive summary, core decisions, acceptance criteria | Production, Management |
| [01](01-engine-baseline.md) | Engine baseline and fork policy | Engineering |
| [02](02-architecture.md) | Module architecture and dependency rules | Engineering |
| [03](03-runtime-systems.md) | Runtime systems: movement, animation, world, AI, audio | Gameplay, Art, Audio |
| [04](04-multiplayer.md) | Server-authoritative multiplayer | Online, Engineering |
| [05](05-rendering.md) | Atom render pass hierarchy | Art, Rendering |
| [06](06-data-schemas.md) | Data, save and protocol schemas | Engineering, QA |
| [07](07-budgets.md) | Performance, memory and network budgets | All |
| [08](08-quality-gates.md) | CI, regression testing and release gates | QA, Production |
| [09](09-roadmap.md) | Engineering sequence, first 12–16 weeks | Production |
| [10](10-risks.md) | Risk register | Production, Management |
| [11](11-scope.md) | Launch scope: Must-have / Should-have / Post-Launch, and the rules that enforce it | Production, all |
| [90](90-source-reconciliation.md) | Source reconciliation: the six contradictions between the source documents, and how each was resolved | Engineering, Production |

## Scope boundary: the combat layer

Phoenix is a first-person action game, so it has a combat layer. This document
specifies that layer **exclusively as abstract game mechanics**: state
machines, authority, damage events, hit validation, cooldowns, spread and
recoil as tuning curves, and the data schemas that carry them.

It deliberately contains no real-world weapon engineering — no manufacture,
procurement, modification or ballistic optimisation of actual firearms. Where
a mechanic needs a number, that number is a gameplay tuning value validated
against game feel and competitive balance, not a physical specification.
Requests to turn this layer into real-world weapon guidance are out of scope
for this document and for the project.

## How to change this document

A change to any decision recorded here needs an ADR in `docs/adr/` and a
pull request that updates both the ADR and the affected chapter. The five core
decisions in chapter 00 additionally need Engineering and Production sign-off,
because the budgets, gates and roadmap all derive from them.
