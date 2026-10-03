# Layers: how the base and your own layers fit together

A **layer** is a git repository with a `groundwork-layer.toml` at its root. A **stack** is an ordered
list of layers. [`just link`](../README.md#quick-start) assembles a stack into `~/.claude/`, where
Claude Code reads it. This repository is the lowest layer, the **base**. Everything below uses
made-up layer names: `acme` for a team layer and `alice` for a personal one.

## What belongs where

The test for any note: is it true for anyone who follows the workflow, or only for you?

| the base holds (neutral mechanism) | your layer holds (your answers) |
| --- | --- |
| The workflow: branches, commits, reviews, releases, session rituals | Which forge, cloud, CI and vendors you actually use |
| Standing principles that hold for any stack | Your jurisdiction, legal entity and licence defaults |
| Templates with placeholders | The filled-in versions, and anything with a real name in it |
| The mechanism: `bin/gwk.py`, `groundwork.just` | Your notes, decisions and the history of your incidents |
| Slash commands that load a workflow | Commands, skills and agents that are yours |

The base is written as a neutral reference: no person's name, no "decided by", no vendor. A lesson
from an incident is kept as the lesson, with the vendor and the people removed. Who decided what,
and with which provider, belongs in your layer. [`CONTRIBUTING.md`](../CONTRIBUTING.md) states the
same rule for contributors.

Two ways to see which side a note is on:

- If a stranger who has never heard of you could follow it unchanged, it is base material.
- If it only makes sense with your accounts, your servers or your name, it is yours.

## The stack

A stack is declared in `groundwork.toml`, which only the **top** layer owns (the one that sets
`assembled = true` and runs `just link`). A lower layer never names a higher one.

```toml
schema = 1

[[layer]]
name = "base"
path = ".groundwork/base"
rank = 0

[[layer]]
name = "acme"
path = "../acme"
rank = 10

[[layer]]
name = "alice"
path = "."
rank = 20
```

- `path` is relative to the directory holding `groundwork.toml`, so a tree of repositories survives
  being moved as a whole.
- `rank` orders the stack, lowest first. Gap the ranks by 10 so a layer can be inserted later
  without renumbering.
- `.groundwork/base` is a relative symlink to the base clone. `just new-layer` creates it, and the layer's
  `justfile` imports the base's recipes through it with `import?` (optional on purpose: on a machine
  without the base, an unknown recipe fails loudly instead of the whole `justfile` becoming
  unparseable).
- A layer with no `groundwork.toml` of its own is still valid. It is a stack of one, or, when it has a
  `.groundwork/base` link, a stack made of the layers beneath it.

`just new-layer <path>` writes a two-layer stack (the base and the new layer). A deeper stack such
as the one above is that file edited by hand, with `assembled = false` set in `acme`'s
`groundwork-layer.toml` so that exactly one layer owns `~/.claude/`.

## The ranks and handles contract

`just link` gives each layer a **handle** under `~/.claude/groundwork/`: its rank as two digits, a
hyphen, then its name. The example stack above gets `00-base`, `10-acme` and `20-alice`.

Handles are what notes and commands use to refer to a layer, because they are stable absolute
paths even when the repositories live somewhere else on another machine. The commands the base
ships import their workflow through the base's handle:

```text
@~/.claude/groundwork/00-base/workflows/session/wrap-up-session.md
```

So **the base must be declared as `name = "base"` with `rank = 0`**. If a stack names it anything
else, every shipped command would load as an empty file and nothing would say so. `just link` and
`just doctor` therefore fail with an explanation instead. `just new-layer` writes it correctly.

Your own layers can be named and ranked as you like, within this much: a name is lowercase
letters, digits and hyphens, starting with a letter, and `base` is taken.

## What `just link` writes into `~/.claude`

Everything is a symlink into a layer, or a generated index, so editing either path edits the same
file and there is no sync step. Re-running it is safe. Anything in `~/.claude` that `link` did not
create is reported and left alone, never deleted.

| in `~/.claude/` | what it is | when two layers provide it |
| --- | --- | --- |
| `CLAUDE.md` | symlink to the entry file | the highest layer that has one wins |
| `settings.json` | symlink to `claude/settings.json`, if any layer has one | the highest layer that has one wins |
| `commands/`, `agents/` | real directories, one symlink per `.md` file | per file name; the higher layer's file replaces the lower one's |
| `skills/` | a real directory, one symlink per skill directory | per skill directory; the higher layer's replaces the lower one's |
| `groundwork/<handle>` | one symlink per layer, to the layer's root | every layer is present |
| `groundwork/ROOTS` | the layer paths, one per line | |
| `groundwork/INDEX.md` | every note in every layer, with its title | |

Notes (the files under a layer's `note_dirs`) are **not** merged: each layer keeps its own, reachable
through its handle. To search all of them, use the paths in `ROOTS`, because `grep -r` and `rg` do
not follow symlinked directories found during recursion but do follow command-line arguments:

```sh
rg 'worktree' $(cat ~/.claude/groundwork/ROOTS)
```

Because the highest layer's entry file wins, **your entry file replaces the base's** rather than
adding to it. That is why the one `new-layer` writes starts by importing the base's.

## Imports: `@~/.claude/groundwork/<handle>/...`

Claude Code expands a line of the form `@path` in a `CLAUDE.md` into the contents of that file.
Layers use the same form in two places:

- **The entry file.** Alice's `claude/CLAUDE.md` begins with the import of the layer below it, then
  adds her own routing. In a stack of three, each layer imports the one beneath:

  ```text
  @~/.claude/groundwork/10-acme/claude/CLAUDE.md
  ```

  and `acme`'s entry file imports `@~/.claude/groundwork/00-base/claude/CLAUDE.md`.
- **Commands.** A command file is a thin wrapper that imports the workflow it triggers, so the
  workflow stays an ordinary note that is readable on its own. The shipped ones also say, in
  plain words, to read that file themselves if the import did not load.

Always go through a handle, never an absolute path: a hard-coded `/Users/alice/...` breaks on every
other machine, and `just doctor` rejects it. `just doctor` resolves each import against the stack
as declared in `groundwork.toml`, so it checks them before and without an assembled `~/.claude`, and it
fails on one that names a handle the stack does not have or a file that does not exist.

## The direction rule

**A lower layer never refers to a higher one.** A base note may name a directory that exists in
every layer (`standards/`) but never a file that exists only in `alice`'s layer, because that file is
one person's answer. `just doctor` checks it for every note in the stack. It is what keeps the
base publishable: take any lower layer on its own and nothing in it dangles.

`just publish-check` is the stricter gate before a layer that sits beneath another is ever pushed
somewhere public. It checks that layer for IP addresses and for the identifiers (owned domains,
emails and repository-name stems) listed under `[publishable]`. It is only as strict as those
lists and cannot catch a leak written in prose.

## `groundwork-layer.toml`

| key | meaning |
| --- | --- |
| `schema` | always `1` |
| `name` | the layer's name; with its rank it forms the handle |
| `note_dirs` | the directories holding notes, declared rather than detected so a missing one fails |
| `entry_file`, `entry_max_words` | the router loaded into every session, and its word budget |
| `assembled` | `true` on exactly one layer per stack: the one that owns `~/.claude` |
| `commit_reference` | `"issue"` (a trailing `(#N)` is required) or `"none"`; the default is `"issue"`. `GWK_COMMIT_REFERENCE` in the environment overrides it. |
| `[map.<dir>]` | `heading` and `purpose` of each directory's generated `MAP.md` |
| `[publishable]` | `domains`, `emails` and `repo_stems` this layer must never leak into a layer beneath it |

The other files a layer keeps in `.groundwork/`: `author-name` and `author-email` (the identity
`just commit` uses, git-ignored), `commit-baseline.txt` (individual commits, by SHA, that predate
the commit rule) and `link-baseline.txt` (wikilink targets known to dangle, each with a reason).
