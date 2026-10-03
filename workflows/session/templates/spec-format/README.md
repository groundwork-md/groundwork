---
title: "The chunked spec format — start here"
type: "reference"
category: "session"
---

# The spec format

A specification that a person can read and an agent can navigate, without either loading all of it.

Read `format.md` for the rules. The files beside it are the templates to copy.

## Why this exists

A 2,001-line single-file spec with 175 functional requirements produced a product that could not
reassign a ticket. The spec described the `assignee` **field** in two requirements and never
described the act of **handing work to someone**. It was long, careful, and structurally blind.

Two things were wrong, and only one of them was about writing:

- **Coverage.** Its eight sections were all about the system — architecture, domain functions,
  interfaces, compliance, release, migration. None was about people. Functional requirements say
  what a system does to data; they never say who does what to whom, in what order.
- **Navigation.** Nobody loads 2,000 lines to implement one feature, so in practice it was consulted
  at the start and then stopped governing anything.

The fix for the first is a **mandatory dimensions block** and a **use-case section**, not more
prose. The fix for the second is **chunking with stable IDs**.

See your layer's `vault/research/` on specification formats for human and agent readers, for the research this rests on.
