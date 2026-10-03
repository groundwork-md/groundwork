---
title: "Repo workflow: bootstrapping a repo"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow.

## Bootstrapping a repo

A repo is **bootstrapped** when it is created for this workflow, and **adopted** when it already has
history. Adoption never touches that history: commits that predate the rules are recorded by SHA
(`commits-and-prs.md`), not rewritten.

1. **Create the repo, private** (`repos-start-private.md`), under the right owner on your host.
   A remote is not a hard prerequisite of the workflow: a repo may live locally until a forge is
   genuinely needed, and the branch rules apply identically. Without a forge there is no pull
   request; the merge is a local plain merge and the review happens on the diff.
2. **Create `production` (the releasable branch) and `development` (the integration branch).**
   Neither is ever committed to directly (`branch-model.md`). The root commit is the one commit
   every repo has, and it must conform to the commit rule like any other, so author it on a working
   branch (`chore/<N>-bootstrap-repository`), not on a protected one.
3. **Pick the tracker and apply its adapter.** The adapter says how issues are identified, which
   status values exist and how they are recorded, and how a milestone is created. With the GitHub
   adapter that is `adapters/github-issues.md`: create the status labels, the type and area labels
   and the first milestone before the first issue is filed.
4. **Set the merge policy.** Plain merge commits only, never squash or rebase-merge, and the merge
   commit's subject must be the pull request's title so that it conforms
   (`commits-and-prs.md`). Where the host offers branch protection or rulesets for your plan and
   visibility, protect `production` and `development` against direct pushes; where it does not, the
   rule is discipline plus a CI check over branch names and commit history.
5. **Declare the releasable packages.** One entry per independently releasable unit: a name, a tag
   prefix, a path glob and a changelog path. A single-application repo has exactly one entry that
   covers everything. See `releases.md`.
6. **Scaffold the task runner** with the repo's standard recipe names (`build`, `test`, `lint`,
   `bootstrap` and so on), so every repo is driven the same way.
7. **Install the commit-msg hook and verify it live.** Install into the repository's common git
   directory (`git rev-parse --git-common-dir`) so that every worktree is covered by one install.
   Then attempt a real non-conforming commit and confirm it is refused, and a real conforming one
   and confirm it lands. "Should work" is not verification. For a layer of this system,
   `just install-hooks` does the install and `just hooks-verify` checks it.
8. **Author the backlog.** For a new project the full backlog is written before any code
   (`workflows/session/start-new-project.md`); the first milestone is the foundation: the licence
   file, the scaffold, and decisions already made that merely need recording.

The hook is deliberately not rolled out to single-branch repos that have no tracker; those get the
type-and-scope half of the rule only (`workflows/single-branch/commit-discipline.md`).

## Why the hook exists

Manual scope-and-reference discipline does not hold under real working pressure, even directly
after an explicit correction: an agent that was corrected for dropping the scope dropped it again
on the very next commit. Only a mechanical check, installed and proven live, keeps the rule true.
