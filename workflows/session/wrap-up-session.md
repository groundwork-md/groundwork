---
title: "Wrap-up-session: routine, non-destructive end-of-session housekeeping"
type: "rule"
category: "session"
---

Distinct from `close-down-session.md` (rare, explicit, destructive full reset of `~/.claude` itself) — this is the routine close for an ordinary working session: git housekeeping, a session-log entry, a rename suggestion. Safe to run often, never deletes anything, and never commits without asking.

**Trigger:** on request ("let's wrap up," "close this out"), or offered at a natural stopping point in the conversation — never silently automatic, since it involves drafting a commit for confirmation. Durable-knowledge capture itself (decisions, preferences, project state) is already continuous via the standing auto-memory system — this workflow doesn't duplicate that; it covers the parts that aren't automatic.

## 1. Git housekeeping — every repo in scope, not just the current one

**groundwork is a stack of repos.** A session that edited a workflow changed the base layer while you were standing in the personal one, and a wrap-up that only inspects `$PWD` reports a clean tree while leaving real work uncommitted somewhere else. That is the failure this section exists to prevent.

Build the list of repos to check:

1. The current repo, if `git rev-parse --show-toplevel` succeeds.
2. **Every groundwork layer**: each path in `~/.claude/groundwork/ROOTS`, if that file exists. These are the layers assembled into the live config; a change in any of them is a change to how every future session behaves.

For each repo in that list, report only if it has something to say — a clean, fully-pushed repo gets one line, not a section:

- `git status --short` and `git diff --stat HEAD` for uncommitted work.
- **Unpushed commits**: `git rev-list --count @{u}..HEAD`. A repo can be perfectly clean and still hold a week of unpushed work; "clean" alone is a misleading summary. Report `no upstream` distinctly from `0` — a local-only repo is a deliberate state, not a problem to fix.
- A drafted commit message (Conventional Commits — `workflows/repo-workflow/commits-and-prs.md` for a repo that tracks work in issues, `workflows/single-branch/commit-discipline.md` if single-branch), scoped to that repo.

**Ask before committing, and ask per repo.** This does not override the standing "only commit when explicitly asked" rule; the draft is offered, not applied. Never push as part of a wrap-up — pushing is its own decision, especially for a layer that is deliberately local-only.

**One mechanical caveat when drafting the command.** `just commit <type> <scope> <message> <paths...>` cannot carry a path containing a space: `just` joins variadic values with spaces before the recipe sees them, so a filename with a space is indistinguishable from two filenames, and the information is gone by then. The vault is full of such filenames. When any path in the set contains a space, draft the direct form instead, keeping the same identity discipline the recipe enforces:

```sh
git add -- <paths>
git -c user.name="$NAME" -c user.email="$EMAIL" commit --author="$NAME <$EMAIL>" -m "..."
```

Never draft `git add -A`.

## 2. Session log entry

Prepend a new entry (newest first) to `SESSION_LOG.md` in the **top layer** — the one holding `groundwork.toml`, last line of `~/.claude/groundwork/ROOTS`. One log for the session, not one per repo: a session is a unit of work, and splitting its narrative across three repos by which files happened to change is how it stops being readable. Fall back to the current repo's root, then `~/SESSION_LOG.md`, if there is no stack. Entry format: date, a short title, a 1-2 sentence summary of what actually happened, and a pointer to the main artifact (a ticket key, a file path, a PR). This is a narrative log, not a duplicate of git history (mechanical diffs) or memory notes (curated standing knowledge) — its job is letting a future session pick the work back up cold without re-reading the whole transcript.

## 3. Close

If any groundwork layer was touched, run `just doctor` in it and report the result. A workflow edit that leaves a dangling pointer is invisible until the next session tries to follow it, and `doctor` is the thing that catches it while the context to fix it is still loaded.

Print a rename suggestion in the format `[YYYY-MM-DD] <project-or-topic> - <what was done>`, ready to paste as the session's name. Print a one-line summary of what happened this pass — repos touched, whether commits were made, whether anything is left unpushed, whether the log was updated. Not a repeat of the conversation, just enough to confirm the wrap-up itself is done.
