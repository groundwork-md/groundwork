---
title: "The scratchpad is shared across rails, and collisions are silent"
type: "hazard"
category: "wave-dispatch"
---

Worktree isolation covers the repository and nothing else. Every rail in a wave is handed the **same session scratchpad path**, so two rails writing a helper script under an obvious name — `probe.py`, `check.sh`, `repro/` — overwrite each other's, and neither is told.

**Confirmed live:** a rail running a sabotage campaign against its own guard had its helper script replaced mid-session by a sibling's. Two of its sabotage runs silently became no-ops — the script still existed and still ran, so nothing errored; it simply tested the wrong thing. The rail noticed only because a result was implausibly clean, re-ran under rail-unique filenames, and got different answers. Had it not noticed, it would have reported two guards as verified that were never exercised.

**Why this is worse than an ordinary race.** The failure mode is not a crash or a missing file — it is a *plausible wrong answer*. It hits hardest in exactly the work that is most valuable in a parallel wave: verification, sabotage runs, before/after reproductions. A rail that loses a scratch artefact mid-verification concludes the verification passed.

**Rule, both halves:**
1. **Namespace every scratch path by rail.** Prefix files and directories with the issue number — `n20-repro/`, `n15-probe.py`. Say so in the brief; do not assume a rail will invent the convention, because the obvious names are obvious to all of them simultaneously.
2. **Never write scratch files inside the repository checkout**, in any worktree. That is a different hazard — it dirties a tree whose cleanliness the orchestrator checks before merging — and the two rules are easiest to state together.

**Also namespace throwaway git repositories.** Rails routinely build a fixture repo to exercise a CLI as a user would (a `<name>_branding` repo, a bare remote). Two rails creating `scratch_branding` in the same directory is the same collision with more state behind it, and a rail that pushes to a bare remote a sibling has since recreated gets a genuinely confusing answer.

**Detection is the hard part and worth stating.** There is no error to catch. The signals are indirect: a sabotage that should have killed a test and did not, a reproduction that stops reproducing, a file whose mtime does not match when the rail last wrote it. A rail that reports "I expected this to fail and it passed" should check for a clobbered scratch file *before* concluding its guard is sound — that is the same class of mistake as trusting a green check that never ran.

See also [[rails-must-be-provably-disjoint]] — disjointness is normally reasoned about in terms of repository files, and this is the reminder that a rail's footprint extends outside the repo.
