---
title: "Regenerable output is bounded where it is made: caches are capped, outputs overwrite, merged worktrees go"
type: "rule"
category: "philosophy"
---

**Why:** a disk filled twice in two days (2026-11-03 on a laptop, 2026-11-04 on a build machine
running five agents in parallel). Both times the cause was the same: build caches, test artefacts
and merged worktrees piled up, and nothing removed them. On the build machine the WSL disk file
filled its whole drive, every agent died, and WSL could not start again until the disk file was
copied to another drive and cleaned. `workflows/session/disk-hygiene.md` cleans up after the fact.
This rule stops the buildup where it happens.

## The rule

Every tool that writes regenerable output limits it itself. Nobody has to remember to clean up.

1. **Caches have a size cap with least-recently-used eviction.** A cache keyed by inputs (built
   trees, per-combination builds, downloaded models, environments) gets a maximum size, set by an
   environment variable with a measured default. When a new entry would pass the cap, the
   least-recently-used entries are deleted first. An entry in use is never evicted. A test proves
   the eviction.
2. **Outputs overwrite, they don't accumulate.** A build or test round writes its artefact under a
   stable name and replaces the previous one. Old rounds are not kept "just in case". What matters
   is recorded instead: a hash in the report, or a tag. Per-round filenames are fine only in a
   bounded scratch folder that is cleared with them.
3. **A merged worktree is removed as part of the merge.** Merging a branch includes
   `git worktree remove` for its worktree, which removes its build output with it, and deleting the
   local branch. A repo that uses worktrees provides one command that removes every worktree whose
   branch is merged.

## How to apply

- **New tools:** when you build a cache, a build step or a test-artefact writer, write its bound in
  the same change. A review of such a change checks for the cap, the overwrite and the eviction
  test.
- **Agent launches:** before launching parallel work, check free disk space, and refuse to launch
  below a threshold. Parallel agents multiply every unbounded output.
- **After the fact:** `disk-hygiene.md` stays the tool for what is already there, including
  orphans this rule cannot see.
- **Not enough on its own:** this rule bounds what is kept. What each run writes, and how parallel
  runs multiply it, is `[[automated-runs-have-a-measured-budget]]`: the same disk filled a third time
  with every cap in place.
