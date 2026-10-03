---
description: Clean up a scrapped (not paused) project's memory across ~/.claude before it goes stale.
argument-hint: <project name>
---

Project being retired: $ARGUMENTS

If no project name was given, ask me which project before doing anything else — this workflow is explicit-trigger only, never inferred from inactivity.

Follow this workflow exactly:

@~/.claude/groundwork/00-base/workflows/session/retire-project.md

If that import did not load, read `~/.claude/groundwork/00-base/workflows/session/retire-project.md` with the Read tool and
follow it — the file above is the workflow, and this wrapper holds no content of its own.