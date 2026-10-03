---
title: "ADR content template"
type: "reference"
category: "repo-workflow"
---

A template for what goes *inside* an architecture decision record. Where ADRs live and how they are cited is the repo's choice; a sensible default is `docs/adr/000N-<slug>.md`, numbered, and referenced by number from code comments, configuration comments and commit messages. The Context, Decision, Consequences form is the long-established one; nothing here is specific to a tool.

**How to apply:** copy the template below for each architectural decision worth a durable record: one settled policy per ADR, not a running log. Keep it short; if Consequences runs long, the decision was probably too big for one ADR. A superseded decision gets a new ADR, and the old one's status is changed to point at it; the old text is never edited to match.

---

```markdown
# ADR 000N: <short decision title>

**Status:** proposed | accepted (as of <date or version>) | superseded by ADR 000M

## Context

<The problem or tension that forced a decision. What was true before, and which constraint or
incident made the status quo untenable. Enough for a reader with no other context to see why
this needed deciding at all.>

## Decision

<The rule itself, stated as something checkable. Not "be careful about X" but "X is enforced by
Y and verified by Z.">

## Consequences

<What this forecloses, what it costs, and what a future change would also have to change. Real
trade-offs, not only upside: an ADR that lists only benefits did not do its job.>
```
