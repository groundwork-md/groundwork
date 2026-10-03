---
title: "Treat maintainability as first-class; favor proactive audits and bold structural change"
type: "principle"
category: "philosophy"
---

Maintainability is a first-class concern, not just "make it work." When a local simplification lands, consider generalizing it into a whole-repo audit for similar wins rather than treating it as a one-off.

Optimize for a maintainable, DRY, low-moving-parts codebase, and stay explicitly open to **bold structural changes** — splitting repos, dropping code generators, deleting dead packages, collapsing lockfile islands — not just timid cleanups.

**How to apply:** lead with the version that removes moving parts. When auditing, rank candidate changes by impact ÷ risk, delete-first. For a genuinely large audit, fan out parallel research across dimensions (topology, duplication, config/codegen/docs) rather than one linear pass. Present a tiered/phased plan and let the size of the change be a real choice, not something decided unilaterally.
