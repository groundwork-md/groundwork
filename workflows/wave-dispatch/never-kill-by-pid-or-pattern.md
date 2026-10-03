---
title: "Never kill a process by PID or name/pattern match"
type: "hazard"
category: "wave-dispatch"
---

Killing processes by PID from `ps aux`, or by name-pattern (`pkill -f "astro preview"`, `pkill -f "hatch run test"`), is never safe in a parallel-rail context — sibling rails very likely run processes with the same name, on the same command. This recurred **four separate times** across different repos/toolchains (a `ps aux`-harvested PID kill, a `pkill -f` by name, a "clean up my background job" `pkill`, and once because the dispatch brief simply omitted the rule that session).

**Root cause pattern:** forbidding one risky pattern (e.g. "don't background") does not imply a related pattern (kill-by-name) is also covered. Each must be named explicitly, every time, in the same standing-rules block — not assumed to follow from another rule, and not left to be "recalled" from a prior session's brief.

**Rule:** never `kill`, `pkill`, or `killall` by PID or name pattern, full stop. If a rail needs to stop something it started, use the harness's own scoped backgrounding/cancellation (e.g. `TaskStop`), never a signal sent by a broad match. This belongs in the standing constraints block of every dispatch brief alongside "no `git add -A`" and "no `git stash`" — not recalled ad hoc per wave.
