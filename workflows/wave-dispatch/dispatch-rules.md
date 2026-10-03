---
title: "Wave-dispatch: the rules for running several agents against one repo"
type: "reference"
category: "wave-dispatch"
---

> Part of `workflows/wave-dispatch/README.md`, applying `workflows/repo-workflow/README.md` to
> several agents at once. **Dormant by default**: single-session work is the norm, and these rules
> apply only when parallel dispatch is deliberately invoked.

## Vocabulary

- A **rail** is one dispatched agent working one issue end to end, on its own branch and worktree.
- A **wave** is a set of issues with no dependency between each other, dispatched together.
- The **orchestrator** is the session that dispatches, verifies and merges. It is a different
  actor from every rail.

## Planning a wave

- **Group by dependency.** Issues in the same wave have no "blocked by" edge between them and may
  run in parallel. Record the grouping as a label (`wave-<n>`), but treat it as a derived
  convenience: the dependency relations are the authoritative data, and if the two disagree the
  relations win.
- **Dispatch in wave order**, and within a wave respect "blocked by" even when the wave number
  alone looks safe. A wave number is a snapshot, not a live recomputation.
- **Cap concurrency.** Up to eight rails per wave, and fewer while the repo is young
  (`new-repo-permission-storm-freezes-rails.md`).
- **Membership requires provable file-level disjointness, not just topical independence**
  (`rails-must-be-provably-disjoint.md`). Two issues that would both edit one shared CI file are
  not parallel-safe. The fix is a design change made when the issues are authored (for instance
  one workflow file per language), not a merge conflict resolved later.

## Status ownership

The ownership split of `workflows/repo-workflow/issue-lifecycle.md` applies unchanged: a rail owns
an issue's status only through `ready` -> `in progress` -> `review`, and the orchestrator owns
`review` -> `done` after verifying and merging. A rail never promotes its own issue
(`issue-lifecycle-ownership-split.md`).

**State transitions are performed centrally by the orchestrator, not by rails.** Several rails
writing to one tracker race each other, and a rail sandboxed to its own worktree cannot reach
anything that lives outside it (`worktree-cannot-reach-sibling-worktree.md`). So the orchestrator
claims each issue before dispatch (`ready` -> `in progress`, read back), moves it to `review` when
the rail reports its pull request open, and owns `review` -> `done`. A rail never writes the
tracker's state at all.

## Work that has no pull request

An issue whose entire deliverable lives somewhere pull requests do not reach (an ADR, a wiki page,
a board restructure on a separate branch) cannot follow the branch and pull-request path, and
concurrent rails would collide on that branch. Such a rail **drafts its artefact to a scratch path
and reports**; the orchestrator commits it centrally. For these issues `review` means "draft ready
for human review", not "pull request open", and `done` follows the human's approval plus the
central commit. One pull request per issue is unaffected: it governs the issues that produce pull
requests.

## Before the first dispatch into a young repo

**Populate the repo's permission allowlist.** An established repo has accumulated hundreds of
approved command patterns, so its rails rarely trigger an approval dialog. A young repo has almost
none, so nearly every path-specific command asks for fresh approval. Dispatch several rails at once
and those requests race: a newer request supersedes a pending one, and the superseded caller hangs
inside its tool call forever, where no message can reach it. Six rails froze that way on one repo's
first day.

Write `<repo>/.claude/settings.json` with the patterns that repo's work actually needs (`git -C <repo> *`,
the worktree paths, the language toolchains, the CLI the adapter uses) before dispatching. Entries match
literally: approving one command does not approve it in a compound, nor against a different path.

Two habits reduce the blast radius regardless: prefer `git -C <abs-path>` and `env -C <dir> <cmd>`
over `cd X && ...` compounds, and give research-only agents no shell at all, since Read, Glob and
Grep never prompt. On that first wave every shell-using rail froze while all four no-shell research
rails finished cleanly, which is the same lesson stated as evidence.
