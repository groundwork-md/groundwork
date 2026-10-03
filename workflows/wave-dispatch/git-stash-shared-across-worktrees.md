---
title: "git stash is shared across worktrees"
type: "hazard"
category: "wave-dispatch"
---

`git worktree` isolates the working tree and index, but **not the stash stack** — there is one stash stack per repository, shared by every worktree. Two parallel rails running `git stash push`/`pop` will silently take each other's entries.

**Rule:** forbid `git stash` outright in any parallel-worktree dispatch. To prove a test fails before a fix: commit the test first and the fix second (history shows it), or copy the file aside (`cp x x.bak`) and restore it, or `git diff > /tmp/<rail>.patch` + `git apply -R`. All are worktree-local.

Also: never leave your own stash entries on the stack while rails are running; check `git stash list` before assuming a worktree's unexpected dirty files mean cross-contamination.
