---
title: "Disk hygiene: reclaim regenerable cache buildup, and consolidate scattered drives into one archive"
type: "rule"
category: "session"
---

Distinct from `close-down-session.md` — that workflow resets Claude Code's own runtime state (`~/.claude`) on explicit request; this one reclaims disk space consumed by ordinary dev tooling (Hatch, Docker, Podman, git worktrees) anywhere on the machine, and is safe to run more casually since everything it touches is either a reproducible cache or confirmed-orphaned data.

## Trigger

Run when disk space gets tight, or periodically as a standing habit — not gated on a full session reset. Doesn't require anyone to notice disk pressure first; if free space looks low during any unrelated task, it's fine to flag this proactively.

## Any machine

The workflow runs on whatever machine is short of space: macOS, Linux, or Windows with WSL. Start by
finding where the space went, not by assuming a path:

- **macOS / Linux:** `df -h` for the volume, then `du -xsh` on the home directory's biggest folders
  (`~/.cache`, `~/Library`, repos, `~/models` or wherever models live).
- **WSL:** inside the distro the same as Linux. On the Windows host, the distro is one virtual disk
  file (`ext4.vhdx`, found with `wsl --manage <distro>` or under `%LOCALAPPDATA%\Packages` or a
  custom folder) that **grows but never shrinks on its own**. Check its size against the host
  drive's free space (`Get-PSDrive`). Deleting files inside WSL frees space for WSL but not for
  Windows, until the file is compacted: `wsl --shutdown`, then `Optimize-VHD -Mode Full` (Hyper-V)
  or `diskpart` → `select vdisk file=…` → `compact vdisk`.
- **A full WSL disk is an emergency:** when the vhdx has filled its host drive, WSL won't start
  and the disk can't even be attached (`ERROR_INVALID_HANDLE`) to clean it. Recovery: copy the vhdx
  to a drive with room, attach the copy to a second, tiny distro (`wsl --import rescue …` an Alpine
  minirootfs, then `wsl --mount --vhd <copy> --bare`), clean it there, compact it, and copy it back.
  Keep the original until the cleaned copy boots. Prevention: `standards/philosophy/bound-regenerable-output.md`.

The paths below are the usual suspects; each lists its macOS and Linux location.

## What to check, in order of typical size

- **Hatch's environment cache** (macOS `~/Library/Application Support/hatch/env`, Linux and WSL `~/.local/share/hatch/env`): one virtualenv per project/environment combo, never auto-pruned, fully reproducible from each project's `pyproject.toml`. Check size (`du -sh`); if it's grown large, clear it — `hatch` rebuilds environments on next `hatch run`/`hatch shell`, cost is just the wait next time each project is touched. **One more cost, found 2026-09-14:** git hooks installed by a Hatch-managed tool (a `commit-msg`, `pre-commit` or `pre-push` hook that execs the environment's Python by absolute path) fail with "No such file or directory" until that project's environment is rebuilt — run `hatch env create` in the project (the path hash is stable, so the hooks resolve again) before the first commit after a clear.
- **Orphaned git worktrees** (`~/*-worktrees/`): for each, check whether the `.git` file's `gitdir:` target actually resolves. A worktree becomes silently orphaned whenever its main repo checkout moves (e.g. into `_archive/`) — `git worktree list` run from the *new* location won't even show it, so these don't self-report as stale. Confirm the branch history isn't uniquely at risk (check the main repo's `git branch -a` wherever it now lives) before deleting — the worktree's working-tree checkout is disposable, but never assume that without checking the branch still exists somewhere.
- **Tool caches** (macOS `~/Library/Caches`, Linux and WSL `~/.cache`): pip, uv, Hugging Face model downloads (`~/.cache/huggingface`, often tens of GB per model), project build caches. All regenerate; a model re-downloads on next use, so check whether it is still needed before deleting.
- **Stale VM-backed container tooling** (Podman machine, Lima, similar): `podman machine list` / `limactl list` show a "last up" timestamp — a machine idle for weeks while its disk image (tens of GB) sits on disk is a strong removal candidate. Confirm nothing depends on it being resumable (check whether the project that used it is still active) before removing.
- **Docker installer/build caches and unused images**: `docker system df` shows reclaimable size directly. Never remove images/volumes still attached to a running container without checking whether that container is itself stale first (an old ephemeral test container left running for days is its own finding, not just a disk one — flag it).
- **Build output inside active repos' worktrees** (`<repo>/.worktrees/*/…/target`, `node_modules`, `dist`, `.angular`): every worktree that ran the project's checks carries its own copy — a Tauri shell's Rust `target/` alone is 2.6 to 4 GB per worktree, and five parallel rails make five of them. All of it is ignored by git and regenerates on the next check or build. Find it with `du -sh <repo>/.worktrees/*` and `git -C <worktree> check-ignore <path>` before removing; `git worktree remove` removes the whole worktree once its issue is done. A project filled a disk this way twice in one day — and a full disk wedges Docker Desktop's VM (its console log can no longer be written, the VM stops, the backend hangs and the app will not relaunch until the hung backend is killed by hand).

## Consolidating drives into one archive

The other half of disk hygiene: not regenerable caches but real data spread over external drives,
old backups and machines, moved into one archive (a cloud drive's sync folder, say) so the drives
can be emptied. A layer can ship tooling for its own drives and archive; the method holds anywhere.

- **Nothing is deleted.** Whatever leaves its place moves into a basket folder on the same drive (a
  rename, so no data is rewritten). The owner empties baskets, never the agent.
- **Sort by metadata, not contents.** Names, sizes, dates and folder structure are enough to sort;
  opening a file's contents needs the owner's permission. A checksum is not reading: a machine reads
  the bytes, nobody looks at them.
- **The checksum is the proof.** Two files are duplicates only when their SHA-256 matches, not when
  name, size and date match. An original goes to the basket only when its copy re-hashed equal *and*
  the sync client reports the copy uploaded (on Windows, the Cloud Files placeholder's in-sync state;
  a file not yet converted to a placeholder is pending, not failed).
- **Make the second run cheap.** Keep a hash cache on each drive (path, size, mtime, hash: re-read only
  what changed) and an index of everything already archived (hash per uploaded file). The first run
  hashes everything; later runs hash the new files and skip whatever the index already holds. Never
  rebuild the index by hashing the archive: online-only files would all download.
- **Dedupe projects whole.** A folder with `.git`, a package manifest or a game world's `level.dat` is a
  unit: identical units collapse, a unit that differs anywhere is archived complete. Deduplicating
  file by file inside it leaves a repository or world with holes.
- **Classify re-downloadable before duplicate.** OS images, installers, drivers and build output go to
  the basket first; otherwise a mirror copy of an ISO looks unique once its twin is gone.
- **Mirrored backup trees are the common case.** Compare whole subtrees by relative path, size and date
  first: it shows which tree is the newest superset, and which rules to write.
- **Windows paths over 260 characters** report no size and fail to copy unless addressed as `\\?\…`.
  Read-only files (git objects) copy read-only, so clear the flag to set timestamps, then restore it.
- **Write maps onto the drives**: a generated `CLAUDE.md` at each drive's root (what it is, its rules,
  one line per top-level folder) and a `MAP.md` per top-level folder, regenerated from an inventory after
  every change, never by hand: a stale map is worse than none, because it gets trusted.

## Prevention

This workflow cleans up after the fact. `standards/philosophy/bound-regenerable-output.md` stops the buildup where it happens: capped caches, outputs that overwrite, merged worktrees removed at merge time. When a cleanup here finds the same kind of buildup twice, the tool that made it is missing its bound: fix the tool.

## What never gets touched here

Real repos and archives (your repos directory and wherever you keep archived projects), any running container's live data, and everything `close-down-session.md` already owns (`~/.claude`). This workflow only ever removes cache/build artifacts that regenerate, or data already confirmed orphaned by cross-checking against where the real thing now lives.

## Confirm before deleting

Same discipline as any destructive action: show what was found and its size before removing it, especially past a few GB or when orphan-status isn't airtight (e.g. a worktree whose branch doesn't obviously exist anywhere).
