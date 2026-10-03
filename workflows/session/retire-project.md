---
title: "Retire-project: clean up a scrapped project's memory before it goes stale"
type: "rule"
category: "session"
---

Triggered by a project actually dying (deliberately scrapped, not paused) — not a session boundary, so it doesn't wait for `wrap-up-session.md` or a periodic `close-down-session.md` run. Without this, a scrapped project's memory sits in `~/.claude/projects/*/memory/*.md` and gets treated as live context in every future session until the next full reset, which could be weeks away.

**Trigger:** explicit only — the maintainer says a project is done/scrapped/abandoned. Never inferred from inactivity; "hasn't been touched in a while" is not the same as "dead," and guessing wrong here means silently deleting real standing knowledge.

## 1. Find every memory file referencing the project

Not just `~/.claude/projects/<repo-slug>/memory/*.md` — search across scopes for `project_<name>*.md` and any other file mentioning the project by name, since memory isn't reliably scoped to one directory (confirmed directly: several real project memories live under the bare home-directory scope instead of a repo-specific one).

## 2. Apply the same decision framework as `close-down-session.md` §2

Reused directly, not re-derived: own-tooling findings drop (now unambiguously — the project's dead), a note that's really a general preference mislabeled as project-specific gets promoted into groundwork instead of deleted, pure project status/decisions drop.

## 3. Confirm, then delete

Same destructive-action discipline as everywhere else — show what's being removed before removing it. This is a scoped version of `close-down-session.md`'s wipe, applied to one project instead of everything.

## 4. The repo itself is a separate, related decision

This workflow only owns memory cleanup. Whether the actual repo gets archived (moved out of your repos directory) is the maintainer's call, made separately — if it does move, `workflows/session/disk-hygiene.md`'s orphaned-worktree check will catch any leftover worktrees pointing at the old path.
