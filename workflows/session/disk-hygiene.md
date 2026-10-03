---
title: "Disk hygiene: periodically reclaim regenerable dev-environment cache buildup"
type: "rule"
category: "session"
---

Distinct from `close-down-session.md` — that workflow resets Claude Code's own runtime state (`~/.claude`) on explicit request; this one reclaims disk space consumed by ordinary dev tooling (Hatch, Docker, Podman, git worktrees) anywhere on the machine, and is safe to run more casually since everything it touches is either a reproducible cache or confirmed-orphaned data.

## Trigger

Run when disk space gets tight, or periodically as a standing habit — not gated on a full session reset. Doesn't require anyone to notice disk pressure first; if free space looks low during any unrelated task, it's fine to flag this proactively.

## What to check, in order of typical size

- **Hatch's environment cache** (`~/Library/Application Support/hatch/env`): one virtualenv per project/environment combo, never auto-pruned, fully reproducible from each project's `pyproject.toml`. Check size (`du -sh`); if it's grown large, clear it — `hatch` rebuilds environments on next `hatch run`/`hatch shell`, cost is just the wait next time each project is touched. **One more cost, found 2026-09-14:** git hooks installed by a Hatch-managed tool (a `commit-msg`, `pre-commit` or `pre-push` hook that execs the environment's Python by absolute path) fail with "No such file or directory" until that project's environment is rebuilt — run `hatch env create` in the project (the path hash is stable, so the hooks resolve again) before the first commit after a clear.
- **Orphaned git worktrees** (`~/*-worktrees/`): for each, check whether the `.git` file's `gitdir:` target actually resolves. A worktree becomes silently orphaned whenever its main repo checkout moves (e.g. into `_archive/`) — `git worktree list` run from the *new* location won't even show it, so these don't self-report as stale. Confirm the branch history isn't uniquely at risk (check the main repo's `git branch -a` wherever it now lives) before deleting — the worktree's working-tree checkout is disposable, but never assume that without checking the branch still exists somewhere.
- **Stale VM-backed container tooling** (Podman machine, Lima, similar): `podman machine list` / `limactl list` show a "last up" timestamp — a machine idle for weeks while its disk image (tens of GB) sits on disk is a strong removal candidate. Confirm nothing depends on it being resumable (check whether the project that used it is still active) before removing.
- **Docker installer/build caches and unused images**: `docker system df` shows reclaimable size directly. Never remove images/volumes still attached to a running container without checking whether that container is itself stale first (an old ephemeral test container left running for days is its own finding, not just a disk one — flag it).
- **Build output inside active repos' worktrees** (`<repo>/.worktrees/*/…/target`, `node_modules`, `dist`, `.angular`): every worktree that ran the project's checks carries its own copy — a Tauri shell's Rust `target/` alone is 2.6 to 4 GB per worktree, and five parallel rails make five of them. All of it is ignored by git and regenerates on the next check or build. Find it with `du -sh <repo>/.worktrees/*` and `git -C <worktree> check-ignore <path>` before removing; `git worktree remove` removes the whole worktree once its issue is done. A project filled a disk this way twice in one day — and a full disk wedges Docker Desktop's VM (its console log can no longer be written, the VM stops, the backend hangs and the app will not relaunch until the hung backend is killed by hand).

## What never gets touched here

Real repos and archives (your repos directory and wherever you keep archived projects), any running container's live data, and everything `close-down-session.md` already owns (`~/.claude`). This workflow only ever removes cache/build artifacts that regenerate, or data already confirmed orphaned by cross-checking against where the real thing now lives.

## Confirm before deleting

Same discipline as any destructive action: show what was found and its size before removing it, especially past a few GB or when orphan-status isn't airtight (e.g. a worktree whose branch doesn't obviously exist anywhere).
