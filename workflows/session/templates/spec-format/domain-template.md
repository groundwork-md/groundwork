---
title: "Template — one spec domain (spec/domains/<name>.md)"
type: "template"
category: "session"
---

# <Domain name>

> Copy this file to `spec/domains/<name>.md`. Keep it under ~300 lines; if it grows past that, it
> is describing more than one domain and splits.

## 1. Purpose

<Two or three sentences. What this domain is responsible for — and what it deliberately is not,
because the boundary is the part people disagree about later.>

## 2. Dimensions

Every row answered. `N/A` is allowed only with a reason.

| Dimension | Answer |
|---|---|
| **Actors** | <Who touches this, in which role. Who explicitly may not.> |
| **Over time** | <How it changes across its life. Who holds it at each stage. What is recorded about the change itself.> |
| **Multiplicity** | <One or many. What happens at **zero**. What happens at an unreasonable number.> |
| **Unwanted** | <What goes wrong. What must happen then. What must *not* happen.> |
| **Not-you** | <Whose workflow differs from the author's: a team rather than one person, a reader rather than a writer, someone on another continent, someone without your tooling.> |

## 3. Enumerations

**Fill these in before writing anything below.** The forcing function is the exhaustive grid, not a
picture — a blank cell is visible in a way a missing sentence is not.

### Transitions

<Every state on both axes. Delete this section only if nothing here has a lifecycle, and say so.>

| from ↓ / to → | `<state-a>` | `<state-b>` | `<terminal>` |
|---|---|---|---|
| **`<state-a>`** | — | ✅ `<what causes it>` | ❌ `<why not>` |
| **`<state-b>`** | ❓ **open** | — | ✅ |
| **`<terminal>`** | ❌ | ❌ | — |

*Mark a cell ❓ when you cannot answer it. That is a finding, and it belongs in §7.*

### Cardinality

<Zero is a column, not a footnote. It is where the interesting answers are.>

| `<Domain>` relates to | Count | At **zero** | At the top end |
|---|---|---|---|
| `<thing>` | 0..n | `<is zero legal? is it normal?>` | `<what breaks at scale>` |

### Actor per step

Carried as a column on every use case in §4. **If one role fills the whole column, that is the
finding** — the domain has no handover and probably should.

### Drawings

<None, or a link. A domain with a table and no drawing is complete; a drawing with no table is not.
Add a drawing when a human will read this domain, or when the shape itself carries meaning.>

## 4. Use cases

### <DOMAIN>-UC-001 — <Actor> <does something>

Actor: <role, citing `ACTORS-00n`>
Goal: <what they are trying to achieve, in their words>

1. <Interaction.>
2. <Interaction.>
3. <System response.>

Fails when: <condition> → `<DOMAIN>-FAIL-00n`

## 5. Requirements

EARS form. Every row traces to a use case or a dimension; one that traces to nothing is a
requirement nobody asked for.

| ID | Requirement | Priority | From |
|---|---|---|---|
| `<DOMAIN>-REQ-001` | The system shall <response> | Must | `UC-001` |
| `<DOMAIN>-REQ-002` | **When** <trigger>, the system shall <response> | Must | `UC-001` |
| `<DOMAIN>-REQ-003` | **While** <state>, the system shall <response> | Should | Dimensions: Over time |
| `<DOMAIN>-REQ-004` | **If** <condition>, **then** the system shall <response> | Must | `FAIL-001` |
| `<DOMAIN>-REQ-005` | **Where** <feature>, the system shall <response> | Could | Dimensions: Not-you |

## 6. Failure modes

Every one becomes a test.

| ID | Failure | Required response |
|---|---|---|
| `<DOMAIN>-FAIL-001` | <what goes wrong> | <what must happen, and what must not> |

## 7. Open questions

| Question | Blocks | Decided by |
|---|---|---|
| <genuinely undecided> | <what waits on it> | <who, or "unassigned"> |

<An empty section is a claim that nothing is open. Usually false, always worth noticing.>
