---
title: "A worktree-isolated rail cannot reach a sibling worktree on another branch"
type: "hazard"
category: "wave-dispatch"
---

A rail isolated to its own feature-branch worktree genuinely cannot reach a sibling worktree checked out from a different branch in the same repo (for example an orphan branch holding wiki or tracker state, checked out beside the code). This is correct harness-level filesystem sandboxing, not a bug to work around.

**Implication:** tracker-state transitions and wiki or ADR writes must stay central. A rail reports what it did, and the orchestrating session is the one that writes the state change, verifies, merges and closes. Do not design a rail's brief around it writing directly to a shared data or wiki worktree; it structurally cannot, and several rails pushing to one such branch would race each other regardless.

The same applies to a layer's `vault/` if it is kept on a separate branch worktree.
