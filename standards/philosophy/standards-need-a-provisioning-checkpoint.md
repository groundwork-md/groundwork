---
title: "A standard written before implementation needs a provisioning checkpoint"
type: "rule"
category: "philosophy"
---

A standing default decided on research alone is a hypothesis. It becomes knowledge only when something is actually built on it. Mark such a standard as provisional, and schedule a real checkpoint at first implementation — otherwise it quietly hardens into fiction that later work gets measured against.

**Why:** a self-hosted platform architecture was resolved carrying the header *"Decided architecture, not yet provisioned."* The first real deployment reversed its central choice within a day — the chosen edge component had an unresolved upstream bug that no amount of documentation review would have surfaced. The research was sound; it simply could not answer the question that mattered.

The specific risk is not being wrong. It is that a confidently-worded standard gets **cited and built upon** before anything tested it, so the error propagates into other notes and repos before first contact with reality. In this case five other files had already adopted the decision as settled fact, and each needed correcting after the reversal.

**Confirmed again, larger blast radius:** the same platform note named a deployment/fleet tool while it was still genuinely unprovisioned (the machine it would run on hadn't even been ordered yet at the time). By the time that tool was actually deployed and then replaced by another, the decision had propagated into **eight** separate files, not the five of the first case, including the entry file `CLAUDE.md` itself, the file loaded into every single conversation. Found by a routine `workflows/groundwork/self-review.md` pass checking "drift between a standing default and what's actually been practiced," not by anyone specifically looking for it — which is itself the strongest argument for keeping that check as a standing, periodic one rather than relying on remembering to update every citing file at the moment a decision reverses.

**How to apply:**

- State provisioning status in the note itself — "decided, not yet provisioned" / "partly provisioned as of DATE" / "in production since DATE". Cheap to write, and it tells a reader how much weight the note actually carries. **Not sufficient on its own**: the platform note *did* carry this header ("Partly provisioned as of DATE") and the citing files still drifted anyway — the header helps a reader of *that* file judge its weight, but doesn't propagate to the other files citing individual tools from within it. The periodic self-review sweep was the actual backstop that caught it, not the header.
- On first real implementation, revisit the note as an explicit step: confirm, amend, or reverse.
- When reversing, **keep the original reasoning visible** rather than deleting it, and say what changed. A reversal with its rationale intact teaches something; a silently rewritten note reads as though the answer was always obvious, which loses the lesson.
- Watch for a standard being cited by other notes before it has been implemented — that is the moment a wrong default stops being cheap to fix.

Complements `[[verify-before-claiming-done]]`: that rule governs claims about *work*, this one governs claims about *decisions*.
