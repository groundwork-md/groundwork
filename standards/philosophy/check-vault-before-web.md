---
title: "Check the vault first, then the web, then write back"
type: "principle"
category: "philosophy"
---

Before researching anything, check `vault/` first for an existing answer — read/grep the relevant notes. Only fall back to a web search on a genuine vault miss. After a real finding (a vault miss resolved via the web, or a first-hand discovery from the work itself), write it back to the vault so the search never has to happen again.

**Why:** a durable, git-tracked knowledge base only stays useful if it's actually consulted before re-researching, and actually grows from what gets learned along the way — not just from deliberate "let's update the docs" sessions.

**How to apply:** when a real finding turns up — not a passing implementation detail, but something worth not re-discovering — write it up as a proper note before ending the turn/task, in the right topic-scoped location per the vault's own structure. Don't under-scope this to "architecture decisions only": bug root-causes, tool gotchas, and useful third-party documentation excerpts belong here too.
