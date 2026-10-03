---
title: "Verify before claiming done: re-run fresh, persist evidence, no vague completion claims"
type: "rule"
category: "philosophy"
---

Never claim a task is complete based on stale output, a prior run, or general impression ("should pass now," "looks good," "the agent reported success"). Before claiming done: identify the actual check that proves it, run it fresh (not cached), read the full output and exit code, and confirm the result actually matches the claim being made.

**Why:** independently converged on by two unrelated agentic-workflow projects researched for groundwork (`obra/superpowers`'s verification-before-completion gate, `get-shit-done`'s `UAT.md` evidence file) — both exist specifically because "claims completion without re-checking" is a real, recurring failure mode, not a hypothetical one.

**How to apply:** for any real check (tests, build, lint, a specific reproduction step), run it in-session and quote the actual result — don't paraphrase or summarize from memory of an earlier run. For anything genuinely un-runnable (a manual/visual check), say so explicitly rather than implying it was verified. This complements, not replaces, `workflows/repo-workflow/issue-lifecycle.md`'s status rules and the review-before-merge discipline — this is about what happens *before* a completion claim is even made, human review is a separate downstream gate.

See also `[[deliberate-break-proofs]]` — a distinct trap in the same family: a guard that has only ever passed hasn't been *verified* to work at all, even if its output was read correctly.
