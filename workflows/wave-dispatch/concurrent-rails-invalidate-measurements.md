---
title: "Concurrent rails invalidate each other's measurements"
type: "hazard"
category: "wave-dispatch"
---

File disjointness prevents rails from corrupting each other's *work*. It does nothing to prevent them corrupting each other's *evidence*: a ticket whose deliverable is a number cannot run beside anything else that loads the CPU — including another measurement ticket, and including the orchestrating session's own builds.

**Confirmed live:** two performance probes in the same wave had to discount their results for contention — one argued from a 6x contention discount rather than report a clean number; another's three timed runs spanned an 18% spread directly attributable to load halving between warmup and timed runs. Both survived only because their margins were roughly 43x — a 20% margin would have been undecidable.

**Rule:**
1. **Never dispatch two measurement tickets in the same wave.** Serialize them even though they're file-disjoint — file disjointness is necessary, not sufficient.
2. **The orchestrating session must stay off the CPU too** while a measurement rail runs. "Just one build" centrally contaminates the number exactly as a sibling rail would; light I/O (docs, ticket authoring) is fine.
3. **Brief the rail to check load itself** (e.g. `uptime`), report the numbers before/after each timed phase, and wait for quiet rather than measure through contention. Give it the quiet threshold explicitly (roughly 1.5× core count) and the likely load source if known.
4. **Report the caveat rather than adjusting the number.** An honest bad number beats a good number obtained by changing the question — say the machine was loaded, by how much, and let the margin carry the verdict, or say the result is undecidable.

This is worse than the resource-collision family (port binding, git stash) in one specific way: those corrupt correctness visibly — something fails. This corrupts only the number, and nothing fails; the number just looks real when it isn't.
