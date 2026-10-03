---
title: "Repo workflow: branch model and worktrees"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow.

## Branches

| Branch | Role | Created from | Merges to | Direct push? |
|---|---|---|---|---|
| `production` | Always releasable | (repo root) | none | **Never**: merge-only |
| `development` | Integration branch for the next release | `production`, at repo creation | none | **Never**: merge-only |
| `feature/<N>-<slug>` | New functionality | `development` | `development` | Yes (it is a working branch) |
| `bugfix/<N>-<slug>` | Non-urgent fix | `development` | `development` | Yes |
| `chore/<N>-<slug>` | Maintenance, build, tooling | `development` | `development` | Yes |
| `documentation/<N>-<slug>` | Documentation only | `development` | `development` | Yes |
| `release/<version>` | Release stabilisation | `development` | `production` **and back into** `development` | Yes |
| `hotfix/<N>-<slug>` | Urgent fix against a released version | `production` | `production` **and** `development` | Yes |

`<N>` is the issue's reference as the adapter spells it, in a form that is safe in a branch name
(for GitHub issues, the bare number). **Branch before the first edit**, not just before the commit.

**Six working families, exactly**: `feature/`, `bugfix/`, `chore/`, `documentation/`, `release/`
and `hotfix/`. The issue's type picks the family: new functionality, tests and epics ride
`feature/*`, bugs ride `bugfix/*`, maintenance rides `chore/*`, documentation-only work rides
`documentation/*`. Spellings such as `feat/`, `fix/` and `docs/` are not families and are
rejected by the name check.

A branch name check (in CI, or the host's rulesets where available) must match names against
the six families. Match with a catch-all that is declared last, so a non-conforming name falls
into the rule that rejects it rather than matching no rule at all and passing unchecked.

## Worktrees

- **Every working branch gets its own worktree, always**, not only for parallel work. The main
  checkout stays permanently parked on `development`: it never checks out a working branch and
  never runs builds.
- **Layout**: `.worktrees/<N>/` inside the repo itself, not a sibling directory, so a repo and
  every branch being worked on it stay together under one path.
- **Create it relative**: `git worktree add --relative-paths .worktrees/<N> -b <family>/<N>-<slug> development`.
  Use `git worktree repair --relative-paths` (or `move --relative-paths`) for one created with
  absolute links. Then the repo as a whole, main checkout plus every nested worktree, can be moved
  with a single `mv`. Verify that the resulting link is genuinely relative rather than trusting
  the flag.
- **`git stash` is forbidden.** The stash stack is shared by every worktree of the repo, so two
  lines of work silently take each other's entries
  (`workflows/wave-dispatch/git-stash-shared-across-worktrees.md`). Use a worktree or a WIP commit.
- Add `.worktrees/` to the repo's ignore rules.

## Currency: rebase private, merge once public

Before a pull request exists, a working branch may rebase onto `development` freely. Once a pull
request is open, only `git merge development` into the branch: pushed and reviewed history is never
rewritten.

Shared branches (`production`, `development`) are never rewritten in the course of ordinary work:
no rebase, no amend, no force-push to clean up. A bad merge is repaired by a forward fix or a
revert commit.

**That prohibition governs ordinary work; it does not claim that a deliberate, whole-repo
remediation can never be authorised.** A shared-branch rewrite requires, without exception:

- the maintainer's explicit per-action confirmation at the moment of the force-push, not merely
  approval of the plan;
- a full mirror backup of every remote, taken first and kept until the result is verified;
- a trial run proving trees are byte-identical before and after, so only messages change;
- a post-push check comparing **every ref's actual SHA** on **every** remote against local, since a
  clean `git push` exit is not proof the remote moved.

Without all four, the ordinary prohibition applies. The standing default for non-conforming
history stays **grandfathering by SHA** (`commits-and-prs.md`): record it and move on. A rewrite is
the rarer, heavier option, chosen deliberately and recorded. One real case: a repo with a few hundred
commits across its shared branches had every non-conforming message rewritten, keeping trees
byte-identical, preserving all tags and keeping each original subject as a trailer; the maintainer was
given the objection and the grandfathering alternative and chose the rewrite.

## Enforcement reality

Whether any of this is enforced mechanically depends on the host: branch protection and rulesets
vary by plan and by repository visibility. Where they are unavailable the rules are discipline, a
CI check over branch names and commit history, and the commit-msg hook. Say which it is in the repo's
`CONTRIBUTING.md` rather than implying protection that is not there.
