# Contributing

Thank you for taking the time. This repository is the **base layer** of a layered knowledge base
(see [`README.md`](README.md) and [`docs/layers.md`](docs/layers.md)). What goes in is
deliberately narrow, so please read the second section before writing anything. Taking part means
following the [Code of Conduct](CODE_OF_CONDUCT.md).

## Licence of contributions

By submitting a contribution you agree that it is licensed under the Apache License 2.0, the same
terms as the rest of the project (see [`LICENSE`](LICENSE) and section 5 of that licence). There is
no contributor licence agreement and no sign-off line to add: nothing to sign.

## What gets accepted: neutral notes only

The base is a reference that other people build their own layer on. So everything in it has to be
true for a stranger, and read that way:

- **No names.** No person's name, no "decided by", no "confirm with <someone>". Address the reader
  as "you" or refer to "the maintainer". A dated decision may stay, unattributed.
- **No vendors.** No hosting provider, identity provider, CI service, registrar or similar product
  in a rule or an example. A tool may be named only where the note is about that tool: an adapter
  file under `workflows/repo-workflow/adapters/`, or Claude Code itself. Your providers, your
  jurisdiction and your own incident history belong in a layer of your own.
- **Keep the lesson, drop the anecdote.** A rule that was learned from an incident states the
  lesson in one sentence. It does not name the product, the project, the person or the ticket.
- **Placeholders in examples.** Use `acme`, `alice`, `example.invalid` and the like. No real
  personal or company data (`standards/philosophy/no-real-pii-in-examples.md`). No absolute paths
  such as `/Users/<someone>/...`, and no assumption about where on disk a person keeps their repos.
- **No secrets, ever.**

A note that fails this test is not rejected for being wrong; it is just not base material. Keep it
in your own layer.

Beyond that, a good note is one topic in one file with `title`, `type` and `category` in its
frontmatter, so an agent can find it with `ls` and `grep`.

## Before you start

- **For anything beyond a small fix, open a GitHub issue first** and describe the change you have
  in mind. This avoids work on something that will not fit. Typos, broken links and obvious fixes
  can go straight to a pull request. Issues are the only place work is tracked.
- **One concern per issue and per pull request.** An issue says what is wrong or missing and where,
  and lists its acceptance criteria as a `- [ ]` checklist. A change mixed with an unrelated
  rewrite is slow to review and hard to revert.
- **Use a branch in your fork**, not your default branch.

## Checks to run before you open a pull request

| What it checks | Command |
| --- | --- |
| The mechanism's own unit tests | `just gwk-test` |
| Frontmatter, wikilinks, referenced paths, `@`-imports, layer direction, maps, entry-file budget, commit history, hooks | `just doctor` (run `just link` once first: it verifies the assembled `~/.claude`) |
| The generated `MAP.md` files match the notes | `just map`, then commit what it changed. Never hand-edit a `MAP.md`. |

Run `just map` after you add, rename or retitle a note. **If a check fails, fix the content rather
than loosening the check.** A check weakened to get one change through stops meaning what it says.
There is no automated CI on this repository yet, so these local runs are the gate.

## Commits

Install the hook once, from your clone: `just install-hooks`.

Every commit subject is a Conventional Commit with a required scope:

```text
type(scope): description
```

This layer sets `commit_reference = "none"` in `groundwork-layer.toml`, so **no issue reference is
required**. A trailing ` (#N)` is accepted if you want to name the issue.

What the `commit-msg` hook enforces, exactly, on the first line of the message:

- the type is one of `feat fix docs style refactor perf test build ci chore revert merge release`;
  any other word is rejected by name (`wip(links): ...`);
- it matches `^<type>\([a-z0-9_-]+\)!?: .+$`: a type from that list, a scope in parentheses made of
  lowercase letters, digits, `_` and `-`, an optional `!` (a breaking change), a colon and a space,
  then at least one more character;
- a missing scope is reported by name (`feat: ...` is rejected, `feat(links): ...` is not);
- a message whose first line starts with `#` passes untouched (git's own comment lines).

What it does **not** check: the length or wording of the description, the body, trailers, or
anything below the first line. The hook is local, installed by `just install-hooks`, and does not run
on a server. `just lint-history` (also part of `just doctor`) audits the history of the whole
repository through the same check.

Accepted: `docs(layers): explain the handle contract`, `fix(gwk): handle an empty input file (#12)`.
Rejected: `docs: explain the handle contract` (no scope), `Docs(layers): ...` (uppercase type),
`wip(layers): ...` (not one of the types), `feat(Links): ...` (uppercase scope),
`Merge branch 'x' into main` (git's default merge message).

`just commit <type> <scope> "<message>" <files>` builds a conforming message and commits exactly the
files you name, but you do not need it: any commit that passes the hook is fine, under your own
identity.

## Pull requests

Title the pull request with a conforming commit subject, since it may become one. The body says what
changed and why, lists the acceptance criteria of the issue ticked only for what you verified, and
says which of the checks above you ran. The maintainers merge with a plain merge commit (no squash,
no rebase), as `workflows/repo-workflow/commits-and-prs.md` describes.

## Reporting a security problem

Please do not report a suspected vulnerability in a public issue or pull request.
[`SECURITY.md`](SECURITY.md) describes the private route.
