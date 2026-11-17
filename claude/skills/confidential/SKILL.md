---
name: confidential
description: Work with a user's confidential documents (tax papers, bank statements, IDs, contracts) without any value reaching the model provider. Use when the user asks to read, summarise, fill in or check a confidential document, or mentions the confidential store, and the layer has enabled [confidential]. Values live in a local store; you only ever handle names like {{ACME_TAX_ID}}.
---

# Confidential documents

Opt-in. Run `python3 ~/.claude/skills/confidential/scripts/confidential.py config` first: if it says
`enabled: false`, stop and tell the user this feature is not switched on in their layer. The full
process is `workflows/confidential/README.md`; the principle is
`standards/philosophy/confidential-values-stay-local.md`.

## Rules

- **You never see a value.** Work with names (`ACME_TAX_ID`), kinds, shapes, counts and verdicts.
- Never read the store or the output directory, by any tool; the guard hook will deny it. Never put a
  value in a command argument.
- Never try to get around `BLOCKED: n matches (...)`. Report it and change what you print.
- If ingest says `seed-phrase suspected in FILE`, tell the user to move it out of that document
  themselves. Do not retry.

## Commands

`C` is `python3 ~/.claude/skills/confidential/scripts/confidential.py`.

| to | run |
| --- | --- |
| learn what a document is | `C ingest FILE` -> category, date, title, a summary with `{{NAME}}` placeholders, names added or reused (label-only categories: category and date only) |
| see what is stored | `C store list` -> names, kinds, shapes |
| rename a stored value | `C store rename OLD NEW` |
| fill a form | write a template with `{{NAME}}`, then `C render TEMPLATE [OUT]` -> `wrote <path>; filled n; missing: [names]`; the user opens the output directory |
| compute with values | write a script using `from confidential import value` (`value("ACME_TAX_ID")`), run `C exec -- python3 script.py`; its output is filtered, so print verdicts and counts, not values |
| check any text before showing it | `C filter` with the text on stdin |

The user adds values themselves (`store add NAME --kind K --from-stdin`) and removes them
(`store remove NAME`); do not run those two. Exit codes: 1 blocked, 2 usage or configuration, 3
seed phrase suspected, 4 local model or text extraction failed.

The scripts run on the machine that holds the store; when that is another machine, run the same
command through `ssh`.
