---
title: "Repo workflow: the issue lifecycle"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow. How a status is recorded and changed is the adapter's
> (`workflows/repo-workflow/adapters/github-issues.md`).

## Statuses

| Status | What it asserts | Notes |
|---|---|---|
| `backlog` | Planning is **not finished**: parked, not yet thought through. | Cannot reach `in progress` directly; promote to `ready` first. |
| `ready` | Scoped, with acceptance criteria, and free to claim. | The opposite claim to `backlog`. |
| `in progress` | Someone has claimed it and is working on it. | |
| `blocked` | Work stopped on a real, named blocker. | Shares the `in progress` column on a board, so a stall stays visible next to the work. |
| `review` | The pull request is open and ready for review. | |
| `done` | **Verified on the integration branch.** | Terminal. |
| `cancelled` | Real work that a deliberate decision chose not to pursue. | Terminal. Needs a one-line reason. |

```text
backlog <-> ready -> in progress -> review -> done
                       |   ^           |
                       v   |           +--> in progress   (review declined: rework)
                     blocked
ready, in progress, backlog -> cancelled
```

`done` is forward-only: a regression found later never reopens a done issue; it becomes a new bug
issue that references the old one. `cancelled` is the only "abandon" status. Do not add a second one
for "was a mistake or a duplicate": say so in the cancellation reason.

## Who may make which transition

- The person or agent **implementing** an issue owns its status only through
  `ready` -> `in progress` -> `review`: claim before starting, move to `review` once the pull request
  is open, **and stop there**.
- **`review` -> `done` is the reviewer's or orchestrator's job alone**, after it has verified the
  work and merged the pull request. An implementer never promotes its own issue to `done`.
- Never leave an issue in `ready` while work is already happening on it.
- **Verify every transition by reading the status back.** The risk is a forgotten write or an
  unauthorised promotion; a write that returned success is not proof it landed.
- When several agents work in parallel, status writes are centralised in the orchestrating session
  (`workflows/wave-dispatch/dispatch-rules.md`).

## Authoring an issue

Every issue is authored complete, at the time it is filed:

- **A body with four sections**: `Scope`, `Approach`, `Acceptance criteria` (a checklist of
  objectively checkable conditions) and `Constraints and prior findings`.
- **A type chosen deliberately**, which picks the branch family (`branch-model.md`).
- **A priority set explicitly**, never left to a default.
- **A milestone**, where the project uses them (`milestones.md`).
- **Labels from the repo's own taxonomy**: exactly one type and at least one area.
- **An assignee set at creation**: planning assigns, claiming does not re-assign.
- **A due date only when a real external deadline exists.**
- **Parents and dependencies, sparingly.** Group the issues of a milestone theme under a parent
  issue. Record a "blocked by" relation only for a genuine, load-bearing technical dependency;
  soft ordering is expressed by milestone and priority, not by edges.

A new issue starts as `backlog` unless it was authored complete in one go, because the author
cannot know whether scoping is finished and the honest default is the unplanned one. Nothing is
migrated retroactively when the vocabulary changes: an issue that was `ready` stays `ready`.

## Claiming

Before any code is touched, for solo work exactly as for dispatched work:

1. Read the issue: require `ready` and no unresolved blocker.
2. Set it `in progress`.
3. **Read the status back to verify.** Only then create the branch and worktree.

A pre-set assignee does not skip the status change: status is the machine, assignment is just who.

## Mid-work discovery

A real bug or gap found outside the current issue's scope: stop and file a new issue immediately,
fully authored, then fix it on its own `bugfix/*` branch with its own pull request. The current
branch never absorbs unrelated fixes. If the current issue is genuinely blocked by the discovery,
set it `blocked`, record the blocker, and flip it back to `in progress` once the fix has merged.

## Review declined

Review feedback is recorded as a comment on the issue, the status returns to `in progress`, **the
pull request stays open** on the same branch and worktree, and the fixes land as new commits. Flip
back to `review` when re-requesting. This loop is unbounded; each decline adds a comment.

A **fundamental rejection**, where the approach itself is wrong: close the pull request unmerged,
delete the remote branch, remove the worktree, then either rewrite the issue's `Approach` and go
again, or cancel it and file a successor.

## Unclaiming

Claimed but genuinely shelved: `in progress` -> `ready`, with a comment giving the reason; close any
draft pull request and remove the worktree. Delete the branch if it holds nothing valuable;
otherwise keep it and say so in the comment.

## Re-scoping

Moving an issue between milestones or parents is free while it is `ready`. After the claim it needs
a comment recording why. It is **forbidden on `done` issues**, because history stays true.

## Closing: the unblock sweep

Closing any issue, whether `done` or `cancelled`, includes a sweep: find every issue that names it
as a blocker. Each hit with no other unresolved blocker flips from `blocked` back to `in progress`
(or `ready` if it was never claimed), with a comment saying what unblocked it, and the new status
is read back.

## Comments are for durable events only

Review-feedback summaries, block and unblock reasons, scope-change decisions and cancellation
reasons. Never chat, and never status-transition noise: the tracker's own history already records
transitions. Ticket-owned artifacts (mockups, benchmark output, specs) are attached to the issue or
committed in the repo, not pasted into comments.
