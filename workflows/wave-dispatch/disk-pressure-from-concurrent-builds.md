---
title: "Concurrent rails exhaust disk, and the failure looks like an unrelated test bug"
type: "hazard"
category: "wave-dispatch"
---

Every rail gets its own `git worktree`, so every rail gets its own build-cache directory (e.g. Rust's `target/`) — build caches aren't shared across worktrees. Six concurrent Rust rails once drove `/` down to 780Mi free (94% full); a rail's test run then died with `ENOSPC`, which reads exactly like a test bug and isn't one.

**Rule:**
- Check `df -h /` before dispatching a wave, and again if any rail reports a strange I/O error. Treat anything under ~5Gi free as wave-blocking, not a warning.
- The orchestrator's own verify worktree is the safe thing to reclaim (`cargo clean` there, or equivalent) — costs only a gate rebuild. **Never clean a live rail's own build directory.**
- Don't clear a shared package cache (e.g. `~/.cargo/registry/src`) while rails are building — it forces re-extraction mid-build and can break them.
- A rail that hits this genuinely isn't at fault and should say so rather than report a false failure.

Same family as the Docker port-collision hazard: concurrent rails interfering through shared machine resources rather than through shared files.
