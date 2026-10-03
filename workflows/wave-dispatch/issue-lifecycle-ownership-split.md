---
title: "A dispatched rail owns its issue's status only up through review"
type: "rule"
category: "wave-dispatch"
---

When dispatching parallel agents against an issue backlog, each rail owns its own issue's status only up through `review`: claim it (`ready` to `in progress`) before starting, move it to `review` once its pull request is opened, **and stop there**.

The `review` to `done` transition is the orchestrating session's job alone, done only after the work has actually been verified and merged. A rail never promotes its own issue to `done`, and an issue must never sit silently in `ready` while work on it is already underway.

**Why:** a dispatched worker is never the one who gets to declare its own work finished; it is the same principle as review before merge, applied to the tracker. It also mirrors "verify status updates landed, never assume": after each transition, read the status back to confirm the write actually happened, rather than trusting that the call succeeded.

**How to apply:** applies to every agent dispatched against a tracked backlog. Ownership split: the rail writes `ready` to `in progress` to `review`; the orchestrator, after verifying and merging, writes `review` to `done`. When several rails run at once, the orchestrator performs all of these writes itself (`dispatch-rules.md`).
