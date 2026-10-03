---
title: "The repo workflow: tracker-neutral rules for how work moves from issue to release"
type: "reference"
category: "repo-workflow"
tags: [workflow, process-standard, gitflow, issues, index]
---

# The repo workflow

How a unit of work travels through a repository: from an **issue**, onto a **branch** in its own
**worktree**, through a **commit** and a **pull request**, into an integration branch, and finally
into a **release**. The rules are the same whichever tracker holds the issues.

**This file is the index.** The rules live in the files below, one topic each, so a reader loads
only the row they need. Nothing in the rule files names a tracker: every tracker-specific mapping
(how an issue is identified, how a status is recorded, which commands move it) lives in one adapter
under `adapters/`. Swap the adapter and the rules stand.

| file | what is in it |
| --- | --- |
| [`bootstrap.md`](bootstrap.md) | The steps that turn an empty repo into one that follows this workflow, and what to verify live. |
| [`branch-model.md`](branch-model.md) | The two long-lived branches, the six working-branch families, worktree-per-branch, and when a shared branch may be rewritten. |
| [`issue-lifecycle.md`](issue-lifecycle.md) | Issue statuses and what each asserts, who may make which transition, and the lifecycle: authoring, claiming, mid-work discovery, rework, unclaiming, re-scoping, terminal states. |
| [`milestones.md`](milestones.md) | What a milestone is, how it is named and closed. |
| [`commits-and-prs.md`](commits-and-prs.md) | **The commit rule.** Conventional Commits with a required scope and an issue reference, no exemption; one PR per issue; review; the merge-to-done sequence. |
| [`releases.md`](releases.md) | Per-package versions, changelogs, the security gate before a production merge, hotfixes. |
| [`file-an-issue-for-every-bug.md`](file-an-issue-for-every-bug.md) | A bug that is not in the tracker does not exist for the project. |
| [`repos-start-private.md`](repos-start-private.md) | A new repo starts private; going public is its own decision. |
| [`adapters/github-issues.md`](adapters/github-issues.md) | **The one adapter.** Issue numbers, branch and commit forms, status labels, and the `gh` commands for every step above. |
| [`templates/`](templates/) | ADR, external-contributor, AI-maintenance-policy and security-policy templates. |

Related: `workflows/single-branch/commit-discipline.md` for repos that deliberately skip branches
and pull requests, and `workflows/wave-dispatch/README.md` for running several agents against one
repo.

**Reading for a specific job?** `claude/CLAUDE.md`'s trigger table points at the right file
directly: committing is `commits-and-prs.md`; bootstrapping is `bootstrap.md`; branching is
`branch-model.md`.

## The vocabulary

The core needs very little from a tracker, and says so, so that any tracker that provides it fits:

- **Issue**: one tracked unit of work with a stable identifier, a title, a body that holds its
  scope and **acceptance criteria**, and a status. "Ticket" and "card" mean the same thing here.
- **Reference**: the issue's identifier as it appears in a branch name, a commit subject and a pull
  request title. Its exact spelling is the adapter's.
- **Status**: where the issue is in its lifecycle (`issue-lifecycle.md`). How a status is recorded
  (a label, a column, a field) is the adapter's.
- **Milestone**: a named group of issues that ship together (`milestones.md`). Optional.
- **Integration branch and production branch**: `development` and `production`, named in
  `branch-model.md`.

## Principles

These are what the rest of the workflow follows from. Each is a rule that was learned by being
violated.

1. **One issue, one branch, one worktree, one pull request.** A unit of work too big for one pull
   request was scoped wrong; split the issue.
2. **The issue is the contract, the diff is the fact.** Acceptance criteria say what was promised;
   what the change actually added is read from the diff and tested from there
   (`standards/philosophy/derive-tests-from-the-code-surface.md`).
3. **Every commit says what and where, and names its issue.** `type(scope): subject`, plus the
   reference, with no exemption for merges or releases.
4. **A status is a claim, and a claim is verified.** After every transition, read the status back.
   "Done" means *verified on the integration branch*, not "the merge button was clicked".
5. **A worker never declares its own work finished.** The agent or person who implements an issue
   moves it to review and stops; verification, merge and closing belong to someone else.
6. **Shared branches are never rewritten in ordinary work.** A bad merge is repaired forward, by a
   new commit or a revert.
7. **Review before merge, and a human does the reviewing.** Green CI is a precondition, not a
   substitute.
8. **A new repo is private until someone decides otherwise.**

## How to amend this

A change that alters a rule needs the maintainer's agreement; fixing a typo or recording a
resolved open question does not. State the reason next to the rule, and keep the lesson, not the
anecdote: an incident that taught a rule belongs in the rule as one sentence, with no names, ids or
tools attached.

Anything that is true only for one tracker goes in that tracker's adapter, never in the rule
files. If a rule file needs a command to be understood, the rule is not neutral yet.
