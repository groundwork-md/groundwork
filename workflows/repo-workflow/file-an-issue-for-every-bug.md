---
title: "File a real issue for every bug found, even if fixed inline"
type: "rule"
category: "repo-workflow"
---

Whenever a bug is found during work, whether it is fixed immediately in the same session or deferred, file a real issue for it in the project's actual tracker. A mention in a report, a commit message or a chat reply is not a filing.

**Why:** a bug mentioned only in passing is real but invisible to the project's backlog: nobody sees it unless they happen to read that specific conversation or commit. A filed issue is part of the durable, queryable backlog instead of something that has to be remembered or rediscovered later.

**How to apply:** before moving on from a task where a bug was found and either fixed or deferred, check whether an issue exists for it, and file one if not. This applies even when the bug was fixed inline in the same session: the fix and its reasoning still belong in the tracker's permanent record, not only in a commit message that takes digging through git history to find. Close such an issue as done immediately if it is already fixed. The point is that the durable record exists, not gatekeeping work that is already finished. If the fix landed on a branch that is not this issue's own, say which commit fixed it in the issue.
