---
title: "Repo workflow: releases"
type: "reference"
category: "repo-workflow"
---

> Part of `workflows/repo-workflow/README.md`. Rules here bind every repo that follows this
> workflow.

## Versions and changelogs

- **Per-package SemVer tags from day one.** Each releasable package (declared at bootstrap,
  `bootstrap.md`) has a tag prefix, for example `core-v`, `server-v`, `website-v`, and its own
  `CHANGELOG.md` in Keep a Changelog format. A single-application repo has exactly one package
  covering everything.
- **Attribution to a package is always by path glob**, never by a commit's scope string. A diff is
  a fact; a scope string is free text a person or agent can get wrong.
- **A changelog entry is required only for merges into `production`**, not `development`, since
  development prereleases do not warrant their own entry.
- **Development prereleases** are cut on merge to `development` as `X.Y.Z-dev.N+<sha>` and never
  move a `latest` pointer.
- **Who creates tags.** Prefer that tags matching a package prefix are created only by the release
  process itself (a release job or one maintainer-run command), and that a human or CI job pushing
  such a tag by hand is rejected. A version check and a changelog check remain as a safety net
  against that process regressing, not as the primary mechanism.

## Cutting a release

`release/<pkg>-vX.Y.Z` branches from `development`, passes the gate below, merges by pull request
into `production` with a merge commit, is tagged **on `production`**, and is then back-merged
`production` -> `development`.

- **Release-gate failure.** A bug found while gating a release is fixed on the release branch via
  its own issue if small. If it is structural, abort: delete the release branch, fix on
  `development`, and re-cut.
- **Hotfixes need issues too.** `hotfix/*` branches from `production`, merges to `production` **and**
  back into `development`, with a patch bump. "No work without an issue" has no 2 a.m. exception.

## The security gate before every `production` merge

A **structured pass plus human approval**:

- A recorded security pass covering at least: a dependency audit, new `unsafe` or foreign-function
  surface, plugin and capability boundaries, a secrets scan, and a supply-chain diff since the last
  release. The findings and a verdict are written into the release pull request body.
- Explicit approval of that verdict by a human (the maintainer) before the merge.

In a team with a dedicated security reviewer that reviewer owns the gate; in a solo repo the pass
is executed in-session and the human approves it. The gate sits on `production`, not on
`development`. It is an organisational layer on top of whatever mechanical checks the host offers,
not something a branch rule can encode.
