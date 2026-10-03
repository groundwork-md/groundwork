---
title: "Bounded fix-loop with an explicit ruling on the final call"
type: "rule"
category: "philosophy"
---

When iterating on a fix/review cycle, don't let it run indefinitely: three rounds at the original approach, then up to two more at a deliberately different angle (a stronger model, a different reviewer, a fresh pair of eyes on the same problem). If it's still unresolved at the end, record an explicit ruling — the decision made, why, and what the cost is if that decision turns out to be wrong — rather than silently picking a direction and moving on.

**Why:** lifted from `obra/superpowers`'s subagent-driven-development skill. Most workflow docs leave "when do we stop iterating and who decides" open; this gives a concrete answer and makes the final call auditable after the fact instead of buried in conversation history.

**How to apply:** applies to any repeated fix/review cycle, solo or with subagents — the round-counting and ruling format are what matter, not the specific "3 then 2" split, which can flex with how expensive each round actually is.
