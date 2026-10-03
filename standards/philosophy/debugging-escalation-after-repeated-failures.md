---
title: "Three failed fixes: stop patching, re-examine the design"
type: "rule"
category: "philosophy"
---

After three attempted fixes for the same problem fail, stop iterating tactically. Something about the understanding of the problem is wrong, not just the fix — the next step is root-cause investigation into the actual design/architecture, not a fourth patch attempt.

**Why:** lifted from `obra/superpowers`'s `systematic-debugging` skill — a concrete numeric trigger rather than "use good judgment," which is easy to rationalize past in the moment (each individual "one more try" feels reasonable; three in a row is a real signal).

**How to apply:** count fix attempts on the same underlying problem, not just failed test runs. When the threshold hits, say so explicitly and switch modes — investigate why the mental model is wrong before writing more code.
