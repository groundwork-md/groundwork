---
title: "Always isolate parallel/background git work into its own worktree"
type: "hazard"
category: "wave-dispatch"
---

Use `git worktree add <path> -b <branch> <base>` for any git-mutating work that runs concurrently with other work in the same repo, rather than letting multiple lines of work share one checkout.

**Confirmed live:** two lines of work (one background agent, one foreground) sharing a checkout had the shared tree's branch silently swapped out from under one of them mid-edit, confirmed via `git reflog`. Both independently converged on the same fix: isolated worktrees. Applies within a single session too (stacking several features on top of each other), not only to genuinely parallel dispatch.

**A subtler failure mode: the primary checkout's branch state is untrustworthy, not assumed.** `main`/`development` can only ever be checked out in the ONE primary worktree, so any rail that needs to touch it — even for a legitimate emergency fix — has to interact with that shared checkout regardless of an instruction not to. One incident: a rail fixed a stray commit on `main` via the primary checkout and left it switched to `development`; the orchestrator then merged from there without re-checking the active branch, landing a merge on the wrong branch silently.

**Rule:** run `git branch --show-current` immediately before every merge/branch-force operation on the primary checkout, every time — even mid-session when you "already know" what branch it's on.

**Also worth knowing independently:** a subagent working in a correctly-isolated worktree can still commit to the wrong branch if its shell's *cwd* silently drifts to a different checkout mid-session (e.g. after reading a reference file from another worktree) and a later git command runs without an explicit `cd` back. If a subagent reports a git behavior that sounds like the harness/git did something inexplicable, cwd drift is the more likely explanation than a genuine worktree bug — check that first.

**Isolation fixes the git-level race; it does not fix a shared dev DB/service** if the repo has one — budget for that separately (defensive test-fixture teardown, don't assume an unrelated failing test is a regression before checking for leftover state from a sibling).

**"Another agent is working on X in parallel," anywhere in a task's own briefing, is the trigger to start in a worktree from the very first branch checkout — not a thing to notice only after a collision is already underway.** Confirmed across three unrelated repos. Corollary: the *absence* of that sentence in a briefing is not evidence of safety — concurrent sessions routinely run against the same shared clone without every briefing naming the others explicitly.

**Even an already-isolated session can slip back into the shared clone by habit** — calling Edit/Write with an absolute path under the shared clone out of muscle memory rather than the worktree path. After entering a worktree, verify the working path before every edit for the rest of the session, not just once at the start; nothing warns you when an edit lands outside the worktree you meant to use.

**Defensive mitigation actually seen working platform-wide:** whichever session must check out over another's uncommitted work should `git stash` it first with a message naming the branch/reason (e.g. `WIP <branch>: stashed by <session> before <reason>`), rather than a bare checkout that lets the other session's work fall through to silent discard. Worth using deliberately as a fallback, not just recognizing it after the fact.

**`git checkout -b <new>` with no explicit start-point forks from whatever HEAD currently resolves to, not from "the branch you meant."** In a shared working directory, a sibling's own `checkout` landing between your last status check and your `checkout -b` silently forks your new branch from their in-progress work instead — no error, no warning, it just resolves the wrong ref. Always pass an explicit start-point (`git checkout -b <new> <base-branch-or-sha>`), and check `git log --oneline -3` immediately after any `checkout -b` in a shared working directory before doing anything else.

**Recovery primitive: `git commit -m "..." -- <exact paths>` beats `git add` + `git commit`** when recovering in a shared clone that might have a sibling's own changes staged at the same time — it commits exactly the named paths' current working-tree content regardless of what else is in the index, so it can't accidentally pull in a sibling's staged files. Stage only exact owned paths in general; never `git add -A`/`git add .` in a possibly-shared checkout.

See also: the general "don't trust the exit code" discipline this is one flavor of, and [[commit-discipline]] (the equivalent for single-branch, direct-commit repos).
