---
title: "Spec format rules: the seven parts of a domain file"
type: "rule"
category: "session"
---

# Spec format rules

## The shape on disk

```
spec/
  README.md              index and navigation — the only file always loaded
  00-context.md          why this exists, who it is for, what it will not do
  01-actors.md           WHO. every role, and what each may do
  02-journeys.md         use cases: sequences of interactions between actors and the system
  03-glossary.md         every term that could mean two things
  04-architecture.md     how it is put together, and what it runs on — optional; software only
  domains/<name>.md      one bounded domain per file
  contracts/<name>.md    interfaces that outlive an implementation
  operations/<name>.md   compliance, release, migration
  decisions/<id>.md      one decision per file, with its cost if wrong
```

**No file exceeds ~300 lines.** When one does, it is describing more than one thing and splits. The
limit is not aesthetic: a file that cannot be loaded alongside the work it governs stops governing.

## Identifiers

`<DOMAIN>-<KIND>-<NNN>` — for example `ITEM-REQ-004`, `ITEM-UC-002`, `ITEM-FAIL-001`.

| Kind | Meaning |
|---|---|
| `REQ` | a requirement, in EARS form |
| `UC` | a use case — one actor, one goal, one sequence |
| `FAIL` | a named failure mode and the required response |
| `INV` | an invariant that must hold at all times |
| `DEC` | a decision, with alternatives and cost if wrong |

**Identifiers are permanent.** A withdrawn requirement is marked withdrawn and keeps its number;
renumbering breaks every ticket, commit and test that cited it.

## Every domain file has the same seven parts

In this order, because the order is the thinking order.

### 1. Purpose

Two or three sentences. What this domain is responsible for, and what it deliberately is not.

### 2. Dimensions — **mandatory, and the reason this format exists**

Five questions, answered for every domain. Not optional, and `N/A` requires a stated reason.

| Dimension | The question it forces |
|---|---|
| **Actors** | Who touches this, in which role? Who may not? |
| **Over time** | How does it change across its life? Who holds it at each stage? What is recorded about the change itself? |
| **Multiplicity** | One or many? What happens at **zero**? At an unreasonable number? |
| **Unwanted** | What goes wrong? What must happen then? What must *not* happen? |
| **Not-you** | Whose workflow differs from the author's — a team rather than one person, a different time zone, a reader rather than a writer, someone without the tools the author has? |

These five are not arbitrary. They are the dimensions repeatedly *not* invented unprompted when a
feature is described as a data field. **Over time** and **Not-you** are the two that caught nothing
in the failing spec and would have caught its worst gap.

### 3. Diagrams — **required, and drawn before the prose**

Produced with your diagramming skill or tool if you have one (otherwise any
text-based diagram format), embedded in or linked from the domain file.

**A diagram is a forcing function, not an illustration.** That is the whole reason it comes before
the prose rather than after it:

- You cannot draw an **ER diagram** without committing to *cardinality* — one or many, and whether
  zero is allowed.
- You cannot draw a **state machine** without naming every state and every transition, including
  the ones nobody wanted.
- You cannot draw a **sequence** or **swimlane** without saying *who acts* at each step — which is
  precisely the question a field-shaped requirement never asks.

Prose can omit all three without looking incomplete. A diagram cannot: the gap is visible as an
unlabelled edge or a missing lane.

#### The enumeration is mandatory; the drawing is how a human reads it

**What forces the commitment is the exhaustive enumeration, not the picture.** A transition *table*
with every state on both axes has exactly the forcing property a state machine has — you cannot
leave a cell empty without seeing that you did. A cardinality table with a `zero` column forces what
an ER diagram forces. A per-step actor column forces what a swimlane forces.

So the rule splits in two:

| | required | form |
|---|---|---|
| **Enumeration** | **always, before the prose** | a table in the domain file |
| **Drawing** | when a human will read this domain, or when the shape itself carries meaning | `diagrams/<name>.html` via the skill |

The enumeration is not a cheaper substitute — it is better for most readers. It **diffs**, so review
sees which cell changed. It **greps**, so an agent finds one transition without loading an image. It
lives in the same file as the requirements, so it cannot drift from them. What it cannot do is make a
shape obvious at a glance, which is exactly what a drawing is for and why both exist.

**A domain with a table and no drawing is complete. A domain with a drawing and no table is not** —
a picture cannot be checked against the requirements mechanically, and nothing fails when the two
disagree.

Each dimension has a diagram type that answers it:

| Dimension | Diagram | What drawing it forces you to decide |
|---|---|---|
| **Actors** | swimlane, or user journey | Who acts, and where one role ends and another begins |
| **Over time** | state machine | Every state, every transition, and which are forbidden |
| **Multiplicity** | ER / data model | Cardinality on every relation, including zero |
| **Unwanted** | state machine (error states) or flowchart | Where a failure lands, and whether it can be left |
| **Not-you** | swimlane with a lane per role | Whether the diagram has exactly one lane — which is the tell |

**Minimum per domain, as enumerations:** a transition table if anything has a lifecycle, a
cardinality table if it has relations, and an actor-per-step column on every use case. A domain that
genuinely needs none says so and why. Drawings are then added where a human audience needs them.

> **First diagram in a new project** triggers the skill's style-guide gate. Settle branding once, at
> project start, rather than being interrupted mid-spec.

### 4. Use cases

One actor, one goal, one numbered sequence of interactions. This is the section whose absence let a
field be specified without anyone noticing it changes hands.

```
### UC-003 — Reviewer takes over a finished ticket

Actor: reviewer (see ACTORS-004)
Goal:  take responsibility for verifying work someone else did

1. The implementer moves the ticket to `review`.
2. The implementer names a reviewer.
3. The system records the handover, with who and when.
4. The reviewer sees the ticket in their queue.

Fails when: no reviewer is named → FAIL-002
```

### 5. Requirements — EARS form

Five patterns. The keyword makes the requirement's kind visible at a glance, and each maps to a
test directly.

| Pattern | Shape |
|---|---|
| Ubiquitous | The `<system>` shall `<response>` |
| Event-driven | **When** `<trigger>`, the `<system>` shall `<response>` |
| State-driven | **While** `<state>`, the `<system>` shall `<response>` |
| Unwanted | **If** `<condition>`, **then** the `<system>` shall `<response>` |
| Optional | **Where** `<feature>`, the `<system>` shall `<response>` |

Every requirement carries an ID, a priority, and the use case or dimension it comes from. A
requirement that traces to nothing is a requirement nobody asked for.

### 6. Failure modes

Each named, with what the system must do. These come out of the **Unwanted** dimension, and every
one becomes a test. Anything that can be refused belongs here rather than being discovered later.

### 7. Open questions

What is genuinely undecided, and what it blocks. An empty section is a claim that nothing is open,
which is usually false and always worth noticing.

## Traceability, both directions

- Every ticket cites the spec IDs it implements.
- Every requirement reaches at least one ticket, or is explicitly deferred.
- A requirement with no ticket and no deferral is unimplemented and invisible — the condition this
  is designed to make impossible.

## How an agent uses this

1. Load `spec/README.md` — always, and only this by default.
2. From the ticket's cited IDs, load the specific domain files. Usually one, rarely three.
3. Load `01-actors.md` and `03-glossary.md` when the work touches people or vocabulary.
4. Read the domain's **state machine and ER diagrams** before its requirements. They carry the
   cardinality and the transitions in a form that is faster to check work against than prose.

Never load the whole tree. If a task seems to need it, the task is too large and splits first.
