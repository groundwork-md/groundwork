---
title: "Commit discipline for single-branch, direct-commit repos"
type: "rule"
category: "single-branch"
---

Applies to any repo that deliberately skips the branch-and-pull-request workflow (`workflows/repo-workflow/README.md`) and commits directly to its one branch: groundwork layers themselves, and any repo of the same shape (lightweight note-taking or wiki-style repos where per-edit branches and PRs would be pure overhead).

## Message format: `type(scope): description`, no ticket reference

A single-branch repo uses the same Conventional Commits rule as every repo that follows the repo workflow (`workflows/repo-workflow/commits-and-prs.md`): **type and scope both required**. It differs only in the trailing issue reference, which is not required because a repo of this shape has no tracker to reference: in the layer's `groundwork-layer.toml` it sets `commit_reference = "none"`. That is the only difference between the two rules, and it follows from the repo's shape rather than being a relaxation of discipline.

A repo of this shape still gets a `commit-msg` hook. "There is no issue key for it to check against" is true of the *reference*, but not of the type and scope, and those are exactly what drifts: a live audit of one such repo's history found **9 of its first 49 commits with no scope at all**, one of them using `standards:`, which is not even a valid type. It is the same failure that the commit rule's hook exists to stop in tracked repos (`workflows/repo-workflow/bootstrap.md`).

**No merge exemption**, matching `workflows/repo-workflow/commits-and-prs.md`. It costs nothing here: the push sequence below rebases onto origin rather than merging, so a repo of this shape does not generate merge commits in normal use.

**How it is enforced:** `just install-hooks` installs a `commit-msg` hook; `just commit` builds a conforming message by construction; `just lint-history` audits the whole history and is part of `just doctor`. Commits that predate the rule and cannot be fixed — this branch is pushed, and rewriting published history is what this document warns against — are listed individually by SHA in `.groundwork/commit-baseline.txt`, never by pattern or date cutoff.

## Identity: never rely on local/global git config

Local git config in a shared or long-lived clone is not a safe place to store identity — whoever set it last silently applies to every subsequent commit from anyone (or anything) using that clone, with no error. Pass identity explicitly on the commit invocation itself, every time, rather than relying on a stored default:

```bash
git -c user.name="<name>" -c user.email="<email>" commit --author="<name> <email>" -m "..."
```

Both `-c user.name`/`-c user.email` (sets the *committer*) and `--author` (sets the *author*) are needed — a commit can silently get the wrong value in either field independently.

## Staging: never `git add -A` / `git add .`

Stage the exact paths actually written, nothing else. This is what protects any other uncommitted work sitting in the same working tree from being swept into an unrelated commit.

## Pushing: fetch-and-check before every push, with a retry loop

Direct-to-the-only-branch has no branch to isolate a push conflict onto, so a naive push can fail — or worse, if the workflow doesn't check first, silently diverge:

```bash
git fetch origin <branch>
git diff --stat HEAD origin/<branch>   # non-empty means something landed since your last pull
git rebase origin/<branch>             # only if there's a real divergence
git push origin <branch>
```

A non-fast-forward push failure is not an error to fight — it means something else landed first. Re-fetch, rebase, retry.

**Live once a remote exists**, not dormant. An earlier version of this paragraph said "currently dormant... which has no remote yet" until a remote was added, and the note was not updated with it — caught by `just lint-paths`' sibling check rather than by anyone re-reading the file, which is the argument for having the checks at all.

`just push` implements this exact sequence, including a final read-back comparing the local SHA against `git ls-remote` — a zero exit code from `git push` is not proof the remote moved.

## Structural: reduce the shared-file surface

If a repo has any file every edit tends to touch (a root index/MOC note, a single "everything" file), that file is the highest-collision point and the most likely place for two concurrent writes to silently clobber each other. Splitting into scoped subtrees that most edits stay within reduces the odds without needing locking — a lesson worth remembering if groundwork's own root `README.md` or any similar index file ever becomes a bottleneck.

See also: the general "don't trust the exit code" discipline, and [[worktree-isolation-for-parallel-work]] (the parallel-dispatch flavor of the same family).
