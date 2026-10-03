---
title: "Close-down-session: mine ~/.claude for durable notes, then wipe and recreate from groundwork"
type: "rule"
category: "session"
---

Invoked on explicit request only — never automatically. Goal: everything durable that accumulated in the live `~/.claude` outside groundwork gets promoted into groundwork properly, then the runtime state gets wiped clean and re-derived from groundwork alone.

## 1. What's in scope

`~/.claude` minus what groundwork owns. **Since the layer split (2026-08-30) groundwork no longer owns four symlinks — it owns one symlink and four assembled directories:**

| path | shape | who recreates it |
| --- | --- | --- |
| `CLAUDE.md` | symlink into the top layer that provides one | `just link` |
| `commands/`, `skills/`, `agents/` | **real directories** of per-entry symlinks, merged across layers | `just link` |
| `groundwork/` | **real directory**: one handle per layer, plus `ROOTS` and a generated `INDEX.md` | `just link` |

This matters because the earlier version of this section defined groundwork's territory as "four symlinks", and under the current layout a literal reading classifies every one of those directories as disposable runtime state. `commands/` was already missing from that list once, on 2026-08-27, and would have been deleted — breaking every slash command including this one. The lesson did not stick because the list was the problem, not its contents.

**The safe framing is regenerability, not ownership.** Everything in the table is rebuilt exactly by `just link` from the manifest, so deleting it is recoverable in one command — but only if §5 actually runs that command. Verify what is really there (`ls -la ~/.claude`) rather than trusting any list here.

Everything else is Claude Code's own runtime state:

- **Tractable, worth mining**: `~/.claude/projects/*/memory/*.md` — the auto-memory system's notes. These are pre-digested (name/description/`type`/`why`/`how to apply`), the same shape as the ~260 notes reviewed to build groundwork in the first place.
- **Not exhaustively mined**: `history.jsonl`, per-session `*.jsonl` transcripts, `sessions/`, `session-env/`. Too voluminous and unstructured to read line-by-line as standing practice. Spot-check a specific session's transcript only if a memory file seems to be missing given known past work, or the maintainer flags something specific — never a blanket "read every transcript" pass.
- **Pure disposable runtime state, never mined**: `cache/`, `telemetry/`, `plugins/`, `tasks/`, `jobs/`, `paste-cache/`, `image-cache/`, `file-history/`, `shell-snapshots/`, `backups/`, `daemon*`, `ide/`, `uploads/`, `chrome/`, `bin/`, `gh-pr-status-cache.json`, `.last-cleanup`. This is Claude Code's own operational data — caches, session bookkeeping, plugin installs — not knowledge. It regenerates on its own; there's nothing to extract.
- **`settings.local.json`: keep it.** Listed here as disposable until 2026-08-30, when a close-down
  found it holding **61 permission allowlist entries**. Deleting it means re-approving every one, and
  a sparse allowlist is not merely tedious — `workflows/wave-dispatch/new-repo-permission-storm-freezes-rails.md`
  documents it freezing six rails permanently, because concurrent approval requests race and the
  superseded caller hangs inside its tool call forever. The allowlist is expensively-accumulated
  operational state, not a cache. Removing a *specific* stale entry is fine; wholesale deletion is not.
- **`settings.json`**: check for anything the maintainer configured (permissions, hooks, env vars, model/theme choices) that isn't a runtime artifact — carry forward manually if so, since it's not auto-regenerated the way caches are. In practice the simplest carry-forward is to leave the file in place rather than delete and rewrite it.
- **`plans/`**: plan-mode plan files. Session artifacts whose substance should already live in tickets and `SESSION_LOG.md` — but confirm before deleting rather than assuming, since a plan for *in-flight* work may be the only written form of it.
- **Any credential-bearing path** (a dotfile holding tokens, a keyring export): never read the contents, never move them into groundwork. Flag their existence to the maintainer and let them decide what happens to them directly.

## 2. Decision framework for each memory note

Apply the same heuristics developed building groundwork from the archived vault — they held up across ~260 real notes:

- **Own-tooling internals are dropped, same as project status.** A finding about the internal behavior of a project/tool the maintainer built themselves (not a third-party dependency) is only relevant if that specific project is still active — check your repos directory for whether the repo still exists before assuming it's dead. If it's genuinely still alive and actively worked on, this rule doesn't apply — use judgment, don't blindly drop just because it's "own tooling."
- **Dead/superseded tools get dropped.** Cross-check any tool/service named in the note against groundwork's actual current standards (`standards/tech/`, `standards/philosophy/`) — if groundwork no longer uses it (a past reset already dropped it, or a `standards/` note says otherwise), the finding is moot regardless of how well-written it is.
- **Genuinely third-party/generic technical findings get kept**, trimmed of whichever project's framing they were found in, filed under `vault/technical/<topic>/` matching the existing subcategories (check `vault/technical/` for the current list before inventing a new one).
- **A memory note framed as project-specific but actually stating a general preference gets promoted**, not dropped — the sass-template review during groundwork's construction found several "project" memories that were really standing philosophy (design taste, work style) mislabeled by where they happened to get recorded. Watch for this pattern specifically; it's easy to miss.
- **Pure project status/decisions get dropped** unless groundwork's own scope has changed to actually track live project state (it doesn't, as of this note — CLAUDE.md deliberately carries no project awareness).

## 3. Checkpoints, not full automation

Don't run this fully unattended. Batch similar decisions (e.g. "these N notes are all dead-tool-specific, confirm dropping all") and check with the maintainer at natural points, the same rhythm used building groundwork the first time — that back-and-forth caught real mistakes (files logged as written that weren't, policy calls worth a second opinion) that a silent automated pass would have missed. Keep a running decisions log for the duration of the session (a scratch file is fine, doesn't need to survive past the session) so nothing gets lost between checkpoints.

## 4. The wipe

Once mining is done and confirmed, this is destructive — **confirm explicitly with the maintainer before running it**, and show what's about to be deleted, same as any other destructive-action discipline.

Delete everything in scope from §1, leaving `CLAUDE.md`, `commands/`, `skills/`, `agents/` and `groundwork/` alone. **Never follow a symlink while deleting** — every entry in those merged directories points into a real layer repo, and removing a target would delete a note from groundwork itself rather than a copy of one. `rm -rf` on a directory of symlinks removes the links; the same command on a followed path removes the source.

Nothing else here needs the "never hard-delete" treatment vault content gets — it is disposable operational state by design, not knowledge.

## 5. Recreate

**Run `just link` from the top layer** (the one holding `groundwork.toml`). It rebuilds the entry-file symlink, the merged `commands/`/`skills/`/`agents/`, and `groundwork/` with its handles, `ROOTS` and `INDEX.md`. It is idempotent, so running it when nothing was touched costs nothing and is the correct default.

Then `just doctor`, which fails loudly on a dangling entry, a handle not in the manifest, or a declared layer whose directory has gone. Everything else Claude Code needs (`cache/`, `sessions/`, etc.) regenerates on its own on next use.

## 6. Final verification

Read `CLAUDE.md` back through the live `~/.claude` path (not the groundwork path directly) to confirm the symlink actually works end to end, not just that the file exists on disk. With layers, also confirm the base's content is reachable — the entry file `@`-imports lower layers, so a working top-layer file is not by itself evidence the stack loaded.

Confirm a slash command still resolves (`ls ~/.claude/commands/`), and that a cross-layer search works: `rg 'pattern' $(cat ~/.claude/groundwork/ROOTS)`. Plain `grep -r` over `~/.claude/groundwork/` will not find layer content — it does not follow symlinked directories — so use `INDEX.md` or the roots.
