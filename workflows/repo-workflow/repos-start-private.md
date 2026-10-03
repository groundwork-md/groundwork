---
title: "New repos start private; flipping to public is a deliberate, separate decision"
type: "rule"
category: "repo-workflow"
---

Whenever a repo gets a remote at all (still not the default: see `claude/CLAUDE.md`'s "local-only by default"), it is created **private**. Making it public is never a side effect of bootstrapping, reaching a milestone, or any other automatic trigger. It is its own explicit decision, made deliberately when the project is actually ready for that.

**How to apply:** at repo-creation time, set visibility to private regardless of the project's eventual intended visibility. When it is genuinely time to flip a repo public, do that as its own confirmed step, not folded into an unrelated task, and run the pre-publish check first (`just publish-check`, for a layer of this system).
