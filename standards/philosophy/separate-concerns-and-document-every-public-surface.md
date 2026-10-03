---
title: "Separate concerns, state variation as data, and document every public surface"
type: "principle"
category: "philosophy"
---

Two standing instructions, recorded together because they fail together: code that mixes concerns is
code whose pieces have no name worth documenting.

## Structure

**Separate the concerns, and give each one a name.** A unit that traverses, decides and reports is
three units wearing one name — and the tell is that it cannot be described in a sentence without
"and".

**State variation as data, not as control flow.** Where a rule, a case or a boundary varies, put the
variation in a table the code iterates, so adding a case means adding an entry rather than editing
the machinery. This is the difference between a function that grows a branch per requirement and one
that never changes again.

**Keep units small enough to be named honestly.** A helper called `outsideDomPackage` is a
specification; one called `check2` is an apology.

## Documentation

**Every exported symbol carries a docstring** — TSDoc for TypeScript, docstrings for Python, dartdoc
for Dart — with parameters and return values named, not just a restatement of the signature.

**Write them so a generator can consume them.** The point is not commentary: it is that API
documentation should be a *by-product of the code* rather than a separate artifact that rots. A
docstring nobody can generate from is a comment with extra ceremony.

**Say why, where why is not obvious.** A signature already says what a function takes. What it
cannot say is that a coalesce is load-bearing rather than defensive, or that a branch exists because
an absent property and an explicitly-`undefined` one are different types. That is what the prose is
for; everything else is noise.

## The part that decides whether either survives

**A convention without a mechanical check is a convention that drifts**, and it drifts silently,
which is the expensive kind. Wherever a documentation or structure rule is worth stating, prefer the
tool that both *produces* the artifact and *fails* on a violation — a doc generator with an
undocumented-export validation is one gate, not two, and the docs cannot fall behind the code
without the build going red.

This is `[[deliberate-break-proofs]]` applied to conventions rather than to tests: a rule that has
never rejected anything is not known to be in force.

## How to apply

Reach for the structured version first rather than cleaning up afterwards — the refactor is cheap
while the code is new and expensive once something depends on its shape. When a rule list, a
mapping or a set of boundaries appears, write it as data on the first occurrence, not the third.
Document an export when you write it, since the reason it exists is never clearer than at that
moment. And when a convention is worth having, ask in the same breath what would fail if it were
violated; if the answer is "review", expect it to drift.
