---
title: "Template — spec index (spec/README.md)"
type: "template"
category: "session"
---

# <Project> — specification

> Copy to `spec/README.md`. This is the only file loaded by default; keep it short enough that
> doing so is free.

**What this is.** <One paragraph: what the product does and for whom.>

**Status.** <Draft / governing / superseded.> Last substantive change: <date>.

## How to navigate

| Looking for | Read |
|---|---|
| Why this exists at all | `00-context.md` |
| Who the people are | `01-actors.md` |
| How work flows through them | `02-journeys.md` |
| What a word means | `03-glossary.md` |
| A specific behaviour | the domain file below |
| An interface that outlives its implementation | `contracts/` |
| Why something was chosen | `decisions/` |

## Domains

| Domain | Responsible for | File |
|---|---|---|
| `<NAME>` | <one line> | `domains/<name>.md` |

## Identifier scheme

`<DOMAIN>-<KIND>-<NNN>`, where kind is `REQ`, `UC`, `FAIL`, `INV` or `DEC`.

**Identifiers are permanent.** A withdrawn requirement is marked withdrawn and keeps its number —
renumbering breaks every ticket, commit and test that cited it.

## Traceability

Every ticket cites the IDs it implements. Every requirement reaches a ticket or is explicitly
deferred. A requirement with neither is unimplemented and invisible.

| Deferred requirement | Until | Why |
|---|---|---|
