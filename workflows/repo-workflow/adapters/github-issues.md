---
title: "Repo workflow adapter: GitHub issues"
type: "reference"
category: "repo-workflow"
tags: [github, issues, gh, adapter]
---

> The one tracker adapter of `workflows/repo-workflow/README.md`. It maps the neutral vocabulary
> (issue, reference, status, milestone) onto GitHub issues and the `gh` CLI, and names the exact
> commands for each step. A different tracker gets a sibling file in this directory; the rule files
> do not change.

Requires the [`gh` CLI](https://cli.github.com/), authenticated for the repo's host
(`gh auth status`), and `git` 2.48 or newer for `git worktree add --relative-paths`.

## The mapping

| Neutral term | On GitHub |
|---|---|
| issue | an issue |
| reference `<ref>` | the issue number: `#42` in a commit subject and pull request title, `42` in a branch name |
| branch | `<family>/<N>-<slug>`, for example `feature/42-link-checker` (`branch-model.md`) |
| worktree | `.worktrees/<N>/` |
| commit subject | `type(scope): subject (#42)` |
| pull request title | the same conforming subject, ending `(#42)` |
| status | a `status/*` label, plus open or closed (below) |
| type, area, priority | `type/*`, `area/*` and `priority/*` labels |
| milestone | a GitHub milestone |
| parent issue | a parent issue with sub-issues, or a task list in the parent's body |
| blocked by | a `Blocked by #N` line in the body, or GitHub's issue dependency relation where available |
| acceptance criteria | a task-list checklist (`- [ ]`) in the issue body, and again in the pull request body |

## Status labels

Exactly one `status/*` label is on an open issue at any time.

| Status | Recorded as |
|---|---|
| `backlog` | label `status/backlog` |
| `ready` | label `status/ready` |
| `in progress` | label `status/in-progress` |
| `blocked` | label `status/blocked` |
| `review` | label `status/review` |
| `done` | issue **closed as completed**, `status/*` label removed |
| `cancelled` | issue **closed as not planned**, with a comment giving the reason |

Create the labels once per repo (`gh label create status/ready --color 0e8a16`, and so on, plus the
repo's own `type/*`, `area/*` and `priority/*` set). `ready` is the only status that is "free to
claim": an issue carrying no `status/*` label at all is unplanned and must be triaged first.

## Commands

```bash
# Author an issue complete (issue-lifecycle.md: body sections, type, priority, milestone, assignee)
gh issue create --title "Short imperative title" --body-file issue.md \
  --label type/feature,area/cli,priority/p2,status/backlog --milestone "M1" --assignee "<login>"

# Claim: ready -> in progress, then READ IT BACK before creating the branch
gh issue edit 42 --remove-label status/ready --add-label status/in-progress
gh issue view 42 --json labels,state --jq '[.state, (.labels[].name)]'

# Branch and worktree
git worktree add --relative-paths .worktrees/42 -b feature/42-link-checker development

# Open the pull request, then move the issue to review
gh pr create --base development --head feature/42-link-checker \
  --title "feat(links): add a broken-link check (#42)" --body-file pr.md      # add --draft for early feedback
gh issue edit 42 --remove-label status/in-progress --add-label status/review

# Review declined: back to in progress, the pull request stays open
gh issue comment 42 --body "Review feedback: ..."
gh issue edit 42 --remove-label status/review --add-label status/in-progress

# Block and unblock
gh issue edit 42 --remove-label status/in-progress --add-label status/blocked
gh issue comment 42 --body "Blocked by #57: ..."

# Merge (plain merge, subject = the PR title), then remove the REMOTE branch only
gh pr merge 77 --merge --subject "feat(links): add a broken-link check (#42)"
git push origin --delete feature/42-link-checker
git worktree remove .worktrees/42          # keep the local branch

# After verifying on merged development: tick the criteria on the issue, then close it
gh issue view 42 --json body --jq .body > body.md      # edit the - [ ] boxes to - [x]
gh issue edit 42 --body-file body.md
gh issue edit 42 --remove-label status/review
gh issue close 42 --reason completed                    # or: --reason "not planned" for cancelled

# Milestones
gh api repos/{owner}/{repo}/milestones -f title="M1 Link checking" -f description="Goal: ..."
gh api -X PATCH repos/{owner}/{repo}/milestones/<number> -f state=closed   # the close sweep
```

Notes that matter:

- **Do not use `Closes #N` or `Fixes #N` in a pull request or commit.** Closing is the explicit step
  in `commits-and-prs.md`, after verification on the integration branch. GitHub only honours the
  keywords when the base is the default branch, so they also misfire on `release/*` and `hotfix/*`
  pull requests.
- **Always pass `--subject` to `gh pr merge --merge`.** The default merge subject
  (`Merge pull request #77 from owner/branch`) does not conform to the commit rule, and the history
  audit then reports it as a violation on a shared branch that can never be rewritten.
  Do not pass `--delete-branch`: it also tries to delete the local branch, which is kept, and fails
  while a worktree has it checked out.
- **Read every label and state change back** (`gh issue view N --json labels,state`), as the lifecycle
  requires. Check the exit code too: `gh issue edit` refuses a label that does not exist, and a script
  that ignores that leaves the issue in its old status.
- **Milestone and parent moves are free while `ready`**; after the claim, comment why.
- **Rate limits.** A scripted burst of `gh` calls can hit the API's secondary rate limit (HTTP 403 or
  429 in `gh`'s stderr). Back off and retry the same call; do not loop in a tight cycle.

## Enforcement on GitHub

Availability of branch protection and rulesets depends on the plan and on whether the repo is
private or public. Where they are not available, state it in the repo's `CONTRIBUTING.md` and rely
on CI jobs over branch names and commit history, plus the commit-msg hook. A pull request on which
no CI run started is not a passing pull request; check `gh pr checks <N>` and
`gh pr view <N> --json mergeable` before treating a branch as ready.

For a repo whose only integration is a stack of pull requests onto each other, merge `development`
into the stacked branch early and often (never rebase once a pull request is open,
`branch-model.md`), and verify `mergeable` after each merge.

## Verify a new adapter setup

A repo is ready when all of these hold, each verified rather than assumed:

1. The labels above exist (`gh label list`).
2. `gh issue create` with a `status/ready` label produces an issue that carries exactly that label.
3. A conforming commit subject ending `(#N)` is accepted by the hook and `fix: nope` is rejected.
4. A throw-away pull request merged with `--subject` produces a merge commit whose subject
   conforms (`git log -1 --format=%s`).
