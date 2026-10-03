---
title: "CONTRIBUTING.md template: external-contributor section"
type: "reference"
category: "repo-workflow"
---

For a project that is open to outside contributions. It is separate from the internal-workflow rules (`workflows/repo-workflow/README.md`: branch model, worktrees, commit rules), which govern how the core team works. This section is what an outsider needs, written so that a first-time contributor can follow it without reading anything else.

**How to apply:** append this section to the project's `CONTRIBUTING.md` once the repo is genuinely public. Replace the placeholder gate table with the project's real checks, and state the licence terms that actually apply. The text below assumes a permissive licence with **no contributor licence agreement**: contributions are accepted under the repo's own licence, as stated in its `LICENSE` file. If a project does require a signed agreement or a sign-off line, that is a deliberate per-project decision to add here, not a default.

---

```markdown
## Contributing from outside the team

Thank you for taking the time. This section is for people who are not on the core team.

### Licence of contributions

By submitting a contribution you agree that it is licensed under the same terms as the rest of
the project, as set out in `LICENSE`. There is no separate agreement to sign.

### Before you start

- **For anything beyond a small fix, open an issue first** and describe the change you have in
  mind. This avoids work on something that will not be accepted. Typos, documentation fixes and
  obvious bug fixes can go straight to a pull request.
- **Use a branch** in your fork. Do not open pull requests from your default branch.
- **One concern per pull request.** A feature mixed with an unrelated refactor or a documentation
  rewrite is slow to review and hard to revert.

### Checks that must pass

CI runs each of these on every pull request, and a pull request is not ready until all pass:

| What it checks | Command |
|---|---|
| <placeholder: the test suite> | `<command>` |
| <placeholder: lint and type checks> | `<command>` |
| <placeholder: the build> | `<command>` |

**If a check fails, fix the code rather than loosening the check.** A check weakened to get one
change through stops meaning what it says.

### Commits and pull requests

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):
`type(scope): summary`, plus the issue reference the project asks for. A good pull request has a
clear title, says what changed and why, states which checks were run, and is up to date with the
default branch.

### Reporting a security problem

Please do not report a suspected vulnerability in a public issue or pull request. `SECURITY.md`
describes the private route.
```
