---
description: Author a complete GitHub issue for the current repo with gh issue create.
argument-hint: <type> <title> [priority/milestone/labels/assignee details...]
---

Issue request: $ARGUMENTS

Create this issue in the *current* repo with `gh issue create`:

1. Confirm that `gh auth status` succeeds and that the current directory is a git repo with a GitHub remote. If either is missing, stop and say so rather than improvising.
2. Read the repo's existing state to fill the mandatory fields: the type, the priority (set explicitly, never defaulted), the milestone (a real milestone read with `gh api repos/{owner}/{repo}/milestones`, never invented), the labels (exactly one `type/*` and at least one `area/*`, matching this repo's existing label set from `gh label list`) and the assignee.
3. Add the relations the lifecycle asks for: a parent issue for a milestone-theme issue, and a `Blocked by #N` line only for a genuinely load-bearing technical dependency.
4. Write the body to a scratch file with the four sections (`Scope`, `Approach`, `Acceptance criteria` as a `- [ ]` checklist, `Constraints and prior findings`), each with real content and none left as a placeholder. Then run `gh issue create --title "<title>" --body-file <file> --label <labels> --milestone "<milestone>" --assignee "<login>"`. Add `status/backlog` unless the issue is authored complete and ready to claim, in which case `status/ready`.
5. Read the created issue back (`gh issue view <N> --json title,labels,milestone,assignees,state`) and report its number and URL to me.

Ask rather than guessing if a field is genuinely ambiguous.

Field rules: `workflows/repo-workflow/issue-lifecycle.md` (what a complete issue is) and
`workflows/repo-workflow/adapters/github-issues.md` (labels, commands). Read them if anything above
is unclear; do not guess.
