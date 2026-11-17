---
title: "Confidential values stay local: the agent works on placeholders, a local model reads, a filter guards the way out"
type: "principle"
category: "philosophy"
---

When an AI coding agent has to work with a person's confidential documents (tax papers, bank
statements, identity documents, contracts), the **values in them never reach the model provider**.
The agent reasons on names and placeholders; everything that touches a real value runs on the
person's own machine. The process that implements this is `workflows/confidential/README.md`. The
feature is opt-in: a layer that does not enable it changes nothing.

## What the agent may see

- **Names** of stored values (`ACME_TAX_ID`), their **kind** (`tax-id`, `iban`), and a
  **non-revealing shape** such as "22 chars, letters+digits". Never a partial value, never a mask
  that keeps real characters.
- **Formats, counts and verdicts:** "the IBAN passes its checksum", "3 of 3 amounts match", pass or fail.
- **Document type and date.** For categories a layer marks label-only, nothing else.
- **A summary that already uses placeholders:** "Notice to `{{ACME_TAXPAYER}}` about a payment to
  `{{ACME_IBAN}}`".

## What the agent must never see

- **A value.** Not in a file it reads, not in a command's output, not in an error message, not in a
  log, not as an argument. A confidential value is the thing, not a hint about it.

## Why a local model's output is still filtered

A local model reading a document is only half the guarantee. Whatever it writes is **read by the
agent and therefore sent onward** to the provider on the next turn. A summary that quotes an account
number is a leak even though the model that wrote it ran locally. So the local model is treated as
untrusted output: its text is rewritten to placeholders, then every byte that is about to reach the
agent passes a **leak filter**: stored values (matched exactly, ignoring case and spacing, and with
punctuation or digits-only normalisation) and deterministic detectors for common value shapes. A
filter that fires blocks the whole output and says only how many matches and of which kinds. The
local model is also reachable only on localhost: a remote endpoint would receive the document.

Computation follows the same rule: a script the agent writes may read values through a helper, but
its output is filtered before the agent sees it, so it should print verdicts and counts, not values.

## What the guard is, and is not

The guard (a hook that denies tool calls naming the store or the output directory) protects against
**accidental exposure**: an agent that reads a file it should not have, or lists a directory it does
not need. It is **not** a defence against a deliberately hostile agent: commands run as the user, and
anything the user can read, a command the agent runs can read. Treat the feature like the practice in
[[secrets-handling-discipline]]: it removes the easy mistakes, and does not replace judgement about
what is run.

## Recovery and seed phrases are never stored

A recovery or seed phrase (a list of 12, 18 or 24 words that restores a wallet or an account) is
worth more than any other value and is never extracted, stored or summarised. When a document looks
like it holds one, ingestion stops, stores nothing and reports only that one was **found in
`<file>`**. The person moves it out of the document themselves.

## Examples stay fictional

Documentation and tests for this feature use only invented data, as
[[no-real-pii-in-examples]] requires: `acme`, `alice`, `example.invalid`, and published
documentation values for formats that carry a checksum.

**Why:** the exposure is permanent and silent. Once a value is in a provider's request log it cannot
be recalled, and nothing on the person's machine shows it left. Every route out (the document, the
local model's text, a script's output, a command line) is cheap to close in advance and impossible to
close afterwards.
