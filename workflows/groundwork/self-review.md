---
title: "Groundwork self-review: periodically surface candidate improvements, never auto-apply"
type: "rule"
category: "groundwork"
---

Adapted from a self-improving meta-skill shared on r/ClaudeAI (`u/rebelytics`: observes work sessions, logs improvement opportunities across every skill including itself, applies them in scheduled autonomous sessions) — deliberately **not** ported as-is. The autonomous-apply part conflicts with the standing "bold structural change, proposed before executed unilaterally" principle. This is the same idea with that part removed: groundwork reviews itself periodically, but every candidate change still gets surfaced for a real sign-off before anything is written — the same draft-then-approve rhythm used to build groundwork in the first place, just triggered proactively instead of only on request.

## Trigger

Periodic, or after a chunk of substantive work (a research sweep, a multi-session project, several corrections in a row) — not gated on the maintainer asking first, similar in spirit to `workflows/session/disk-hygiene.md`. Not worth running after every small session; the input needs enough accumulated material to be worth a pass.

## What a review pass actually scans

- **Recent conversation/session content since the last review**: repeated corrections that should already be a `standards/philosophy/` note but aren't yet, decisions made ad hoc mid-task that should be codified, gaps noticed in passing but not acted on at the time.
- **Memory files accumulated since the last review** (`~/.claude/projects/*/memory/*.md`) — the same material `close-down-session.md` mines at reset time, but caught earlier/incrementally instead of only at a full wipe.
- **External tools/repos researched along the way** (evaluated and adopted, evaluated and declined, or extracted-not-adopted) — cross-check against existing notes for redundancy, contradiction, or a genuinely new gap, the same way today's `just`/`unlazy`/`get-shit-done`/`superpowers`/`OpenSpec` sweep was handled.
- **Drift between a standing default and what's actually been practiced** — if real work keeps diverging from a documented default, that's either a default that needs updating or a default being ignored for a real reason worth writing down.

## Surfacing non-obvious connections with graphify

Run `graphify` (`claude/skills/graphify/`) against `vault/`, `standards/`, and `workflows/` as part of the scan — its community detection is well-suited specifically to what explicit `related:`/wikilink cross-references miss: two notes that share an underlying concern but never got linked to each other. Use `--update` for incremental reruns once a graph already exists from a prior review pass, rather than a full rebuild every time. `graphify-out/` is a generated, regenerable artifact — gitignored, not committed, same treatment as any other derived build output.

Findings feed into the same output as everything else in this workflow: a candidate (in this case, "these two notes/files look related and aren't cross-referenced — worth a link, or worth merging, or worth nothing") surfaced for review, never an automatic edit.

## Output: a compiled list, not silent edits

Each candidate tagged as addition / edit / restructure / retire, with the reasoning, presented together — mirroring the actual pattern used throughout groundwork's construction: research or observation, then synthesis, then a real review round (drafted content shown in full, or an `AskUserQuestion` when there's a genuine either/or), only then written.

## What never happens automatically

No autonomous edits, no deletions without flagging first, no note silently superseding another without saying so and cross-referencing what it replaces. The mechanism this note adapts is "notice and surface improvements on a schedule" — the "apply them autonomously" half stays explicitly out of scope.

## Reviewing a stack of layers

Since 2026-08-30 groundwork is a stack of repos, not one. A review that walks only the current
directory covers one layer and silently reports the others as fine.

- **Scan every layer**: `rg 'pattern' $(cat ~/.claude/groundwork/ROOTS)`, or read
  `~/.claude/groundwork/INDEX.md` for what each layer holds. Plain `grep -r` over `~/.claude/groundwork/`
  finds nothing — recursive search does not follow symlinked directories.
- **Run `just doctor` in each layer**, not just the top one. `direction` and `map --check` are
  per-layer, and a lower layer can be red while the top is green.
- **Check the base is still publishable**: `just publish-check` in the base layer. An owned
  identifier reaching it is the failure mode with the largest blast radius here, and it arrives by
  ordinary drift — someone pastes a worked example that happens to name a real host.
- **Watch for content in the wrong layer.** The signal is a reference that had to be reworded to
  satisfy the direction rule: if a base note now says "your layer's `standards/legal/`" where it
  wants to name a specific fact, either the fact belongs lower or the note belongs higher. Both are
  real fixes; the wrong one is leaving the vague wording and forgetting why it is vague.
