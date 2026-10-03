---
title: "Dispatch parallel rails only when provably disjoint"
type: "hazard"
category: "wave-dispatch"
---

"Different feature area" is not sufficient grounds to run rails in parallel — a rail that deletes or retypes a shared symbol breaks siblings invisibly, at collection/build time, not at the file level any diff-based check would catch.

**The rule, in priority order:**
1. **One rail per package** (each service/app/library gets at most one concurrent rail).
2. **At most one migration per wave.**
3. **At most one rail touching a shared chokepoint file** (a router registry, a central schema file — anything every new feature also has to edit).
4. **A rail that deletes, renames, or retypes a shared symbol runs ALONE in its package** — no concurrent rail may touch anything importing it.
5. **Shared write primitives are serializing** — anything changing the commit/push/worktree machinery itself, or a pre-receive hook, runs alone.

**Confirmed live:** a 12-rail wave chosen by "feature area" collided five ways on shared files (tedious, recoverable) and once invisibly — one rail retired a bridge symbol while two earlier-branched rails still imported it, so the merged tree failed at collection and stranded the entire integration suite.

**How to apply:** before dispatching, list each candidate's owning package and ask "does any rail here remove something another rail uses?" If yes, serialize it. The safe wave size is roughly the number of independent packages, not the number of independent-sounding tickets — fewer rails that merge cleanly beats more rails plus a multi-hour reconciliation. If a chokepoint file recurs as the bottleneck, that's a signal to split it structurally (per-domain modules, auto-discovery instead of a manual registry) rather than keep working around it every wave.
