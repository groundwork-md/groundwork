---
title: "Rails stall forever if they end their turn waiting on a background notification"
type: "hazard"
category: "wave-dispatch"
---

A rail that starts long-running work in the background and ends its turn "waiting for the notification" stalls permanently — its turn is already closed, so the completion event has nowhere to land. The work finishes fine on disk; the rail just never comes back to commit or report.

**This recurred persistently across many waves, through several tightening passes:**
- Naming the concept ("don't background it") wasn't enough — rails still reached for the `Monitor` tool without classifying that as backgrounding.
- Naming specific tools wasn't enough — rails improvised equivalents by hand (a raw shell `command &` plus a manual polling loop).
- Behavior-level wording ("never put a command in the background by any means") reduced but didn't eliminate it — budget for roughly 30-40% of rails needing one recovery nudge on a long-running full-suite step, as a standing tax, not a bug to fully engineer away.
- A genuinely different mechanism also causes the identical symptom: the **harness itself** auto-backgrounds any Bash command exceeding its foreground timeout (120s by default) — no prohibition on the rail's own choices helps here, because the rail never chose to background anything.

**Rule, both halves:**
1. **Prohibition:** never put a command in the background by any means — not `Monitor`, not `run_in_background`, not a trailing `&`, not `nohup`, and never self-poll a process waiting for it. Run verification synchronously, in-turn.
2. **Positive counterpart:** pass an explicit `timeout` (up to the tool's max) on any command that might run long, so it never crosses the auto-background threshold in the first place. If one auto-backgrounds anyway: re-run it in the foreground with a raised timeout, or split it into stages that each fit — don't wait for the notification, don't kill the backgrounded run.

Also worth including in every brief: **name which check actually covers the rail's own diff** — a rail whose diff touches no Rust shouldn't block its whole report on a formality full-workspace Rust check.

**Recovery when a rail does stall:** check `git status` in its worktree (the work is usually intact, uncommitted), then resume it with `SendMessage` telling it to finish synchronously — plus any state that changed underneath it while stalled (sibling merges, moved migration heads). Resuming carries full context, so it picks up cleanly.
