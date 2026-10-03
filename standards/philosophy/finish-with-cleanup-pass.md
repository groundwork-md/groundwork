---
title: "Always end a non-trivial task with a dedicated cleanup pass"
type: "rule"
category: "philosophy"
---

Before considering any non-trivial task done, run a dedicated final cleanup pass as its own explicit step — don't fold it into the feature edits themselves.

1. **No stray files** — check for uncommitted scratch/temp artifacts; keep git-ignored generated files out of the commit.
2. **Sweep all relevant standing-instruction docs** (not just the ones directly touched) for anything now inaccurate; fix doc/code drift noticed along the way.
3. **Loose ends — connectivity**: verify each new piece is actually wired to the next, not merely present (exports reachable, every call site updated, nothing silently left on the old default).
4. **Loose ends — tests**: confirm no missing cases (both branches, edge values); add them; run the full test gate.
5. **Comments**: rewrite now-misleading doc comments, add short *why* comments where genuinely non-obvious; match existing density — no what-it-does narration.

**How to apply:** add these as explicit end-of-plan steps and actually execute them before commit/handoff, rather than treating "the feature works" as the finish line.
