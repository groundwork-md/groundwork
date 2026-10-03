# groundwork

groundwork is a layered knowledge base of plain markdown files for working with AI coding agents.
It is a git repository of notes (workflows, standing principles, slash commands) plus a small Python script that
assembles them into the `~/.claude/` directory that [Claude Code](https://claude.com/claude-code)
reads at the start of every session.

**The problem it solves.** What you learn about working with an agent (how a branch is named, why a
check that has only ever passed proves nothing, which of your tools bite) normally lives in chat
history or in a tool's opaque memory. It cannot be reviewed, diffed, shared or restored, and it
disappears with the session. Here it lives in files under version control: each note is one topic,
an agent finds it with `ls` and `grep`, and `just doctor` fails when the notes drift (a broken link,
a note that names a file that no longer exists, a map out of date).

**Why layers.** Some of what you know is true for anyone (the commit rule, how an issue moves).
Some is only true for you (your hosting provider, your jurisdiction, your incident history). One
repository cannot be shared without leaking the second kind, so they live in separate repositories
that are stacked when loaded. This repository is the shareable bottom layer, the **base**. You add
a **layer of your own** on top.

```
  ~/.claude/        what Claude Code reads; built by `just link`, symlinks into the layers
      ^
      |  on the same path, the higher layer wins
  +--------------------------------------------------------------+
  |  your layer      rank 10   private                           |
  |                  your vendors, jurisdiction, notes, findings |
  +--------------------------------------------------------------+
  |  base            rank  0   public (this repository)          |
  |                  workflow, standards, commands, mechanism    |
  +--------------------------------------------------------------+
       A lower layer never refers to a file that exists only in a higher one.
       `just doctor` enforces this.
```

More layers can sit in between (a team layer under a personal one). The details are in
[`docs/layers.md`](docs/layers.md).

## Requirements

| tool | version | used for |
| --- | --- | --- |
| `git` | 2.48 or newer | `git worktree add --relative-paths`, which the repo workflow uses; the mechanism itself needs any recent git |
| `python3` | 3.11 or newer | `bin/gwk.py`: the checks and the assembler. Standard library only (`tomllib`), no packages to install |
| [`just`](https://just.systems/) | 1.27 or newer | the task runner (`import?` and `source_directory()`); developed on 1.58 |
| [Claude Code](https://claude.com/claude-code) | recent | reads `~/.claude/`; developed with 2.1.287 |
| [`gh`](https://cli.github.com/) | recent | only for the GitHub-issues adapter of the repo workflow |

Developed and tested on macOS. Everything `just link` writes is a symlink, so it needs a file
system that has them.

## Quick start

Clone this repository anywhere (it is the base), then create your own layer from the clone.
Nothing below writes outside `~/.claude/` and the directory you name.

```sh
git clone https://github.com/groundwork-md/groundwork
cd groundwork

just new-layer ~/my-layer     # an empty layer stacked on this clone, with `git init`
cd ~/my-layer

just install-hooks            # the commit-msg hook (`just doctor` reports it missing until you do)
just map                      # generate each directory's MAP.md
just link                     # assemble ~/.claude from the stack
just doctor                   # every check; it verifies the assembly, so `link` comes first
```

`just doctor` should end with `all checks clean`. Start a Claude Code session and the base's entry
file and slash commands (`/new-issue`, `/wrap-up-session`, ...) are loaded.

To make the first commit, `just commit` needs an identity. It never reads git config, because
whoever set that last silently applies to everyone using the clone:

```sh
export GWK_AUTHOR_NAME="Your Name" GWK_AUTHOR_EMAIL="you@example.com"
just commit chore layer "start my layer" $(git ls-files --others --exclude-standard)
```

(To keep the identity, set those two variables when you run `just new-layer`: it then writes them
to `.groundwork/author-name` and `.groundwork/author-email` in your layer, which are git-ignored.)

`new-layer` writes everything you would otherwise hand-write:

```
my-layer/
  groundwork-layer.toml     what this layer is: its note directories, its entry file, commit_reference
  groundwork.toml           the stack, lowest rank first: base (rank 0), then this layer (rank 10)
  justfile             `import? '.groundwork/base/groundwork.just'`: every recipe comes from the base
  .groundwork/base          a relative symlink to the base clone
  claude/CLAUDE.md     your entry file; it imports the base's, then adds your own routing
  vault/ standards/ workflows/   your notes, each with a README to start from
  SESSION_LOG.md
```

## What is in the base

| directory | what it holds |
| --- | --- |
| `standards/philosophy/` | Standing principles that hold for any stack: verify before claiming done, prove a guard by breaking it, derive tests from the code surface, secrets handling, bounded fix loops. |
| `workflows/repo-workflow/` | A tracker-neutral repo workflow: one issue per unit of work, branch families, a worktree per branch, Conventional Commits with a required scope, one pull request per issue, review before a plain merge, releases with a security gate. `adapters/github-issues.md` maps it onto GitHub issues and `gh`. `templates/` holds ADR, CONTRIBUTING, SECURITY and AI-maintenance-policy templates. |
| `workflows/session/` | Session rituals (start a project, wrap up, close down, retire a project, disk hygiene, a brand-identity process) and the specification-sheet templates. |
| `workflows/single-branch/` | The commit discipline for repos that commit straight to one branch, such as a layer. |
| `workflows/wave-dispatch/` | Rules for running several agents against one repository, each learned from a failure. |
| `claude/CLAUDE.md` | The entry file: a router of at most 400 words that points at the notes by situation. |
| `claude/commands/` | Slash commands that load a workflow: `/new-issue`, `/start-new-project`, `/wrap-up-session`, `/close-down-session`, `/retire-project`, `/disk-hygiene`, `/new-brand-identity`, `/groundwork-self-review`. The base ships no agents or skills. |
| `bin/`, `groundwork.just` | The mechanism: `gwk.py` (checks and `link`), the `commit-msg` hook, and the recipes every layer imports. |

Every directory has a generated `MAP.md` listing its notes by title. Start there, not here.

## Build your own layer on top

`just new-layer` gives you the skeleton above. Put your vendors, your jurisdiction, your decisions
and your incident notes in it, never in the base. Your `claude/CLAUDE.md` replaces the base's entry
file in `~/.claude/` and imports it with `@~/.claude/groundwork/00-base/claude/CLAUDE.md`, so keep that
line. One contract holds the stack together: the base must be named `base` at rank 0 in
`groundwork.toml`. `just link` and `just doctor` fail with an explanation if it is not. What belongs
where, what `just link` writes and how imports resolve is in [`docs/layers.md`](docs/layers.md).

## Everyday recipes

Run `just` for the full list.

| recipe | what it does |
| --- | --- |
| `just doctor` | every check: frontmatter, wikilinks, referenced paths, `@`-imports, layer direction, maps, entry-file budget, commit history, hooks |
| `just map` | regenerate each directory's `MAP.md` from the notes' own frontmatter |
| `just link` | assemble `~/.claude` from the stack; safe to re-run after any layer moves |
| `just install-hooks` | install the `commit-msg` hook; `just hooks-verify` checks that it is live |
| `just commit <type> <scope> "<message>" <files>` | commit exactly the files named, with explicit identity, never `git add -A`; a trailing `(#N)` is added from a `<family>/<N>-<slug>` branch when the layer requires one |
| `just new-layer <path>` | create an empty layer stacked on this base |
| `just migrate-from-heimathafen <layer> [--dry-run]` | rewrite a layer built on the former heimathafen base to the groundwork names; see [`docs/migrating-from-heimathafen.md`](docs/migrating-from-heimathafen.md) |
| `just gwk-test` | the mechanism's own unit tests |

A layer's own configuration lives in `groundwork-layer.toml`; its keys are documented in
[`docs/layers.md`](docs/layers.md).

## What this is not

- **Not a package or installer.** You clone it. There is no registry, no upgrade channel and no
  update command: a layer is a repository you own, and you pull the base when you choose to.
- **Not a framework.** No runtime, no daemon and no dependencies beyond git, Python and `just`.
  The content is markdown; the mechanism is one script.
- **Not an agent or an orchestrator.** It runs nothing on its own. The wave-dispatch notes are
  rules for you and your agents, not a dispatcher.
- **Not an issue tracker.** The repo workflow assumes one and ships an adapter for GitHub issues
  only. Another tracker needs its own adapter file.
- **Not tool-neutral.** The notes are plain markdown that anything can read, but the assembly
  targets Claude Code's `~/.claude/` layout and `@`-imports.
- **Not a security boundary.** `just publish-check` is a denylist over a layer's text: it catches
  listed identifiers and IP addresses, not a leak written in prose.
- **Not your opinions.** The standards are one working set of principles. Replace or extend them in
  your own layer.

## Contributing, security, licence

Contributions are welcome under the rules in [`CONTRIBUTING.md`](CONTRIBUTING.md): generic,
neutral notes only, since vendors and names belong in your own layer. Report a vulnerability as
described in [`SECURITY.md`](SECURITY.md). Everyone taking part follows the
[Code of Conduct](CODE_OF_CONDUCT.md).

Apache License 2.0; see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). There is no contributor
licence agreement: contributions are accepted under the same licence (section 5 of the licence).

groundwork is an independent project, not affiliated with or endorsed by Anthropic. Claude and
Claude Code are trademarks of Anthropic.
