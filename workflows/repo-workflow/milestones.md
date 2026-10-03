---
title: "Repo workflow: milestones"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow. Milestones are optional; a repo with no use for them skips this file.

## What a milestone is

A named group of issues that ship together. It exists so a project can say, at a glance, what a
phase is for and when it is finished.

**Naming**: `M0`, `M1`, `M2`, ... in build order, each with a short phase title (`M3 Release
readiness`). `M0` is the foundation: the licence file, the scaffold, and decisions already made
that merely need recording. It is **not** "CI is always the first issue": the first issues are
whatever the project genuinely needs first, and CI is set up when a real need for it shows up.

**Content.** Each milestone's description holds:

- **Goal**: one paragraph on what the milestone produces and why it gates what comes after.
- **Scope**: a bullet list of concrete deliverables.
- **Exit criteria**: objectively checkable conditions, never "done when it feels done". Prefer
  statements such as "every seeded record round-trips" or "the dependency graph has no cycles".
- **Depends on**: the specific blocking issues or milestones and *why*, not just "M0".

The list of member issues is the tracker's own query (every issue carrying the milestone); it is
not hand-maintained in the description.

## Statuses

A milestone uses the issue status vocabulary (`issue-lifecycle.md`) where it has an equivalent:
`backlog` (declared, deliberately not yet scoped), `ready`, `in progress` (the first member issue
was claimed), `blocked` (a real cross-milestone blocker), `review` (the close sweep is underway),
`done` and `cancelled` (descoped, with the reason recorded). Where the tracker only has open and
closed, those two plus the description are enough; do not invent a status field for them.

**A milestone with no member issues is legitimate only when it is `backlog` or terminal.** An empty
`ready` milestone claims that planning is finished while holding nothing, which is a contradiction
worth failing a check over.

## The close sweep

When a milestone's last issue reaches a terminal status:

1. Confirm that every member issue is terminal; name each one that is not, and stop.
2. Close the parent issue of each theme (a parent moves to `in progress` when its first child is
   claimed and to `done` here, by hand; nothing derives it).
3. Close the milestone itself.
4. Run the unblock sweep (`issue-lifecycle.md`) for anything the milestone was holding.
