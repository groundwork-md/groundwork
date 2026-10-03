---
title: "Repo workflow: commits and pull requests"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow. `<ref>` stands for the issue's reference as the adapter spells it
> (`workflows/repo-workflow/adapters/github-issues.md`).

## The commit rule

Every commit subject is a Conventional Commit with a **required scope** and the issue's reference:

```text
type(scope): subject (<ref>)
```

- `type` is one of `feat fix docs style refactor perf test build ci chore revert merge release`.
- `scope` is required. A subject without one (`feat: add link check`) is rejected, because a
  scope-less example in the rules themselves is exactly how scope-less commits spread.
- The trailing reference names the issue the commit belongs to. A release commit references the
  release (`release(app): 1.2.0 (<ref>)`).
- **There is no exemption. Every commit message conforms, merges and releases included.**
  Conforming forms: `merge(recipes): branch recipes into development (<ref>)` and
  `release(app): 1.0.0 (<ref>)`. No pattern change is needed for those, since `merge` and `release`
  are already valid types, so dropping the exemption deletes a special case rather than adding an
  accepted form.

**Branches and commits both name the issue**: the branch is `<family>/<ref>-<slug>`
(`branch-model.md`), the commit subject ends in `(<ref>)`.

### Reference style is configurable

A repo that has no tracker (a single-branch notes repo, `workflows/single-branch/commit-discipline.md`)
has nothing to reference. The commit-msg hook shipped with this system reads the style from the
layer's `groundwork-layer.toml`:

```toml
commit_reference = "issue"   # a trailing (#N) is required   (the default)
commit_reference = "none"    # no reference required; a trailing (#N), if present, is accepted
```

`GWK_COMMIT_REFERENCE` in the environment overrides the file. Everything except the trailing
reference is identical in both modes.

### Message generation must be controlled too

Git and every forge auto-generate merge messages that conform to nobody's convention, so removing
the merge exemption alone does not tighten discipline: it makes merging impossible. Found
concretely: with the exemption gone and nothing else in place, git's own
`Merge remote-tracking branch '...' into HEAD` was rejected and blocked three merges, a failure
first misread as three merge conflicts.

Two things close that, and adopting the rule in a repo without both is a mistake:

1. **A forge merge takes its subject from the pull request title**, which this file already
   requires to be a conforming subject carrying the reference.
2. **A local merge derives its subject from the branch's own issue commit**, or is written by hand
   in the conforming form.

### Non-conforming history already on a shared branch

A commit that has already landed non-conforming on a shared branch is treated as permanent: shared
branches are never rewritten in ordinary work (`branch-model.md`). List such commits **individually
by SHA** in the history baseline, and count them in their own bucket in the history audit. **Never
grandfather by pattern or date cutoff**: a pattern silently exempts future commits of the same
shape, which is the drift the rule exists to stop.

Grandfathering does not hide anything, because the audit reports those SHAs in their own bucket
and the count stays visible. The wrong instinct is to refuse to grandfather "so the problem stays
visible": that produces an audit that can never go green, which trains everyone to ignore it just
as reliably as a falsely green one. An always-red check is not a more honest check. An authorised
whole-repo rewrite is the heavier alternative (`branch-model.md`); do not reach for it to avoid a
grandfather list.

## Pull requests

- **1 PR = 1 issue, a hard rule.** Every pull request closes exactly one issue. `release/*` and
  `hotfix/*` pull requests are the only exceptions; they reference the release instead. An issue
  too big for one pull request was scoped wrong: split the issue.
- **Every pull request links its issue.** Nothing is merged that cannot be traced to one.
- **Open ritual.** The title is the conforming commit subject, ending in the reference. The body
  carries the issue's acceptance-criteria checklist, ticked only for what was verified, how it was
  verified, and notes for the reviewer. The same step moves the issue `in progress` -> `review`,
  read back.
- **Draft pull requests are allowed** for early feedback. The issue stays `in progress` until the
  pull request is marked ready; that moment is the move to `review`.
- **Never rely on a forge's auto-close keywords.** Closing is an explicit step after verification
  (below), never inferred from a merge event: a merge button click is not the same as "verified on
  the integration branch", and a keyword also misfires when the target branch is not the default.
- **Review before merge, by a human.** The medium is free (terminal diff, web UI, desktop tool).
  Green CI is a hard precondition, not a substitute.
- **Plain merge commits, never squash and never rebase-merge**, so each branch's commits and the
  fact that it was merged both survive in history.
- **After merge, delete only the remote branch**; keep the local branch and remove the worktree.

## Before the pull request opens

- **Test inventory.** The acceptance criteria are a *subset* of what needs testing, never the
  whole. Walk the diff and list everything the change **added**: every command, flag, entry point
  and error path. Then confirm each was executed with real inputs, not only refused. Every entry
  point needs a **success**-path test, because refusal tests prove the guard and never the thing
  guarded. Where the surface is enumerable, write a completeness guard that walks it, so the next
  addition fails loudly instead of being forgotten. When unsure whether something is already
  covered, write the test again: a duplicate costs seconds, a gap costs a release
  (`standards/philosophy/derive-tests-from-the-code-surface.md`).
- **Use it once as a user would**, on something that is not this repository, before closing an
  issue that changes a user-facing surface. A development repository is pre-populated and hides
  every first-run and empty-state defect: one release shipped four defects this way, three of which
  appear only on a fresh project.

## Merge to done

In order. The sequence refuses to reach `done` while any acceptance criterion is unchecked, and
verifies that the branch is genuinely contained in the base rather than trusting that a pull
request was marked merged.

1. Plain merge the pull request, with the pull request title as the merge commit's subject.
2. Delete the **remote** branch only; remove the worktree; keep the local branch.
3. **Verify the acceptance criteria against the merged integration branch**: actually run the
   checks, not "they passed before the merge".
4. Tick the acceptance checkboxes on the issue itself, not only in the pull request.
5. Set the issue to `done` (closed as completed), and read the result back.
6. Run the unblock sweep (`issue-lifecycle.md`).

`done` means "verified on the integration branch", not "merge clicked".

**Post-merge verification failure**: the issue does not reach `done`. It goes back to
`in progress`, and if the merge broke the integration branch itself, an immediate `bugfix/*`
forward fix (or a revert commit) follows. Shared-branch history is never rewritten.
