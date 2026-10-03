---
title: "Reconciling a component-naming collision: merge or rename?"
type: "rule"
category: "wave-dispatch"
---

Even after warning rails in advance about a shared-sounding component name, the collision can still happen exactly as predicted — multiple rails independently building a component with the same name because a shared spec pointed them at it. Resolving it correctly requires diagnosing which of two situations you're in, and they need opposite fixes.

**Diagnose by diffing the full implementations, not just the names:**
- **Genuinely the same component, two independent drafts** (prop shapes and rendered structure close enough that a reader would call them "the same thing, two drafts," each with complementary strengths one is missing from the other) → **merge the best of both** into one canonical file, update the losing call site(s) to the winning prop shape.
- **Same name, genuinely different components** (prop shapes, DOM structure, and interaction model actually diverge, even though the name and the spec section they cite are identical — they solved different real needs that happened to get the same generic name) → **do not hand-merge.** Rename one of them and update its own call sites. Forcing these into one component means one side losing real, independently-verified behavior for no actual benefit.

**How to apply:** when a wave-dispatch brief warns about shared-sounding names, expect the collision to actually happen anyway and budget real orchestrator time after the wave lands to resolve it — this is a genuine design read on whether two same-named things are actually the same thing, not a git-conflict-resolution formality. Verify the resolution against the real built output (not just that the merge/rename compiles) before closing anything.
