# Migrating private layers from heimathafen to groundwork

This base used to be called heimathafen. If you have layers stacked on the old base, this page
takes them over to the new names, one layer at a time, and says how to undo it. Nothing here is
needed for a layer created with `just new-layer` from this base.

Read the whole page before you start. The commands are the ones the migration was tested with, on
copies of two real layers and a scratch `HOME`.

## What changes

Only the names of the mechanism change. A layer keeps its own name, its repository name and the
wording of its notes.

| before | after |
| --- | --- |
| `hafen-layer.toml` | `groundwork-layer.toml` |
| `hafen.toml` | `groundwork.toml` |
| `.hafen/` (state directory, including `.hafen/base`) | `.groundwork/` |
| `hafen.just` (imported by each layer's `justfile`) | `groundwork.just` |
| `bin/hh.py` | `bin/gwk.py` (the program is called `gwk`) |
| `just hh-test` | `just gwk-test` |
| `~/.claude/hafen/` (handles, `ROOTS`, `INDEX.md`) | `~/.claude/groundwork/` |
| `HH_AUTHOR_NAME`, `HH_AUTHOR_EMAIL`, `HH_COMMIT_REFERENCE`, `HH_PROJECTS_DIR`, `HH_BRANCH` | `GWK_AUTHOR_NAME`, `GWK_AUTHOR_EMAIL`, `GWK_COMMIT_REFERENCE`, `GWK_PROJECTS_DIR`, `GWK_BRANCH` |
| `HAFEN_LAYER` | `GWK_LAYER` |
| `/heimathafen-self-review` and `workflows/heimathafen/` | `/groundwork-self-review` and `workflows/groundwork/` |

The base handle keeps its form: `00-base`, the ranks and the `@~/.claude/groundwork/<handle>/...`
import syntax are unchanged apart from the folder name.

## What the migration does

`just migrate-from-heimathafen <layer>`, run from the new base clone, rewrites one layer:

- renames the layer file, the stack file (top layer only) and the state directory;
- repoints `.groundwork/base` at this base when it named the old base. A link to a middle layer
  stays as it is, and `--base <path>` names the new base explicitly;
- rewrites an exact table of references in every text file of the layer, markdown and
  `CLAUDE.md` included: `~/.claude/hafen`, the three file names, `.hafen/`, `bin/hh.py` and `hh.py`,
  the `HH_*` and `HAFEN_LAYER` variables, `hh-test`, the commands of the program that preceded
  `hh.py` (`hafen map`, `hafen doctor`, `hafen publish-check`, ...), and the two moved base files;
- replaces the generated header of each `MAP.md`, so `map --check` stays green without
  regenerating anything;
- adds `commit_reference = "none"` to the layer file when it has no such key. The old mechanism
  required a scope and never an issue reference, which is what `"none"` means; without the line the
  new default (`"issue"`) would fail the whole history. Change it to `"issue"` if the layer tracks
  its work in issues;
- leaves **dated records** as they are written (see [Dated records](#dated-records));
- prints every change, with counts per kind. `--dry-run` prints the same list and writes nothing.

It never commits, never stages and never touches `.git`. It refuses to apply to a directory that
is not the top of a git repository or whose working tree is not clean, so the migration is the only
diff you will see. A dry run on a dirty tree works and warns that a real run would refuse. It also
refuses an old base (a directory that ships `hafen.just` or `bin/hh.py`): the old base is replaced
by this one, never migrated in place.

What it does not do, on purpose:

- It leaves every other word of your notes alone: a layer called "heimathafen" stays so, prose that
  mentions the old name stays, and so do the German word "Hafen" and names such as `linkhafen`.
  A reference followed by `:<digits>` (`hh.py:1007`) cites a line of the old file and stays too.
- It cannot tell a record from a note by reading it. Dated records are kept by their file names
  only, so a log or an audit under any other name is rewritten like a note; add it with `--exclude`
  (below) or restore it before step 8 with `git checkout -- <path>`.
- It does not fix notes that point at files the old base had and this one does not (see
  [What `doctor` can still report](#what-doctor-can-still-report)).
- It does not touch anything outside the layer: your shell profile, `~/.claude/settings.local.json`,
  other repositories' `CLAUDE.md`, CI. Search those for `hafen`, `HH_` and `HAFEN_LAYER` yourself.

## Dated records

A session log, an audit or a set of rulings says what was true on its date. If it quotes `.hafen/base`
or `~/.claude/hafen`, that is the record, so the migration keeps these files as written:

- **By default:** a file named `SESSION_LOG.md`, and any markdown file whose name carries an ISO date
  after a hyphen, `*-YYYY-MM-DD*.md` (`audit-2026-10-03.md`, `rulings-2026-09-20.md`). The month and
  day are checked, so `-2026-13-45` is not a date. A date set off by a space, such as
  `Capability Matrix 2026-08-12.md`, names a "facts as of" note that is kept current; it is not matched
  and is migrated like any note. Look through your layer for such names before the first run, with
  `find <layer> -name '*[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*' -not -path '*/.git/*'`.
- **`--exclude <glob>`**, repeatable, for anything else. A glob without a `/` matches the file name at
  any depth (`--exclude 'decision-log.md'`); a glob with a `/` matches the path from the layer root
  (`--exclude 'vault/projects/old/*'`). `*` also matches `/`. A glob that contains a space cannot go through
  `just` (it joins the arguments with spaces); call `python3 bin/gwk.py migrate-from-heimathafen <layer> ...` for that.
- **`--no-default-excludes`** switches the default off, if you want every dated record rewritten too.

The plan lists each file it keeps, and how many replacements it did not make, on a `would keep` line
(`kept` once applied) and in the `kept as written` count. A file with nothing to rewrite is not listed.
The layer file and the stack file cannot be excluded: they carry the layer's settings, so an
`--exclude` that matches them is refused before anything is written.

`doctor` treats dated records the same way. A `` `path` `` or a `[[wikilink]]` in a dated record that
points at something that no longer exists is not a failure: it is printed, with its count and file, as
kept history. The same reference in a living note still fails, and a dated record still needs its
frontmatter.

With `just migrate-from-heimathafen`, the options go after the layer:

```sh
just migrate-from-heimathafen <layer> --exclude 'decision-log.md' --dry-run
```

## Before you start

- A clone of this base, anywhere. `just gwk-test` should pass in it.
- Every layer committed and clean (`git status` prints nothing). Each layer, middle layers included,
  is migrated on its own; the order does not matter, but all of them before `link`.
- `just` 1.27 or newer, `python3` 3.11 or newer, `git`.
- A quiet machine: `link` rewrites `~/.claude`, so no Claude Code session should be starting.

The steps use these names. Set them for your own paths, lowest layer first:

```sh
NEW_BASE=~/src/groundwork                  # the clone of this base
LAYERS=(~/src/team-layer ~/src/my-layer)   # every private layer; the last one is the top layer
TOP=~/src/my-layer                         # the one holding hafen.toml and running `just link`
```

(`LAYERS=(...)` is bash and zsh syntax.)

## The switch

### 1. Back up and record

```sh
BACKUP=~/groundwork-backup-$(date +%Y%m%d-%H%M%S); mkdir -p "$BACKUP"
n=0; for layer in "${LAYERS[@]}"; do
  n=$((n+1)); cp -a "$layer" "$BACKUP/layer-$n"
  echo "$layer $(git -C "$layer" rev-parse HEAD)" >> "$BACKUP/heads.txt"
done
ls -l ~/.claude ~/.claude/hafen > "$BACKUP/assembly.txt"
cat "$BACKUP/heads.txt"
```

`heads.txt` holds the commit each layer had before. The copies include `.git`. Nothing below needs
the old base, so leave it where it is.

### 2. Check the new base

```sh
cd "$NEW_BASE" && just gwk-test
```

### 3. Preview each layer

```sh
cd "$NEW_BASE"
for layer in "${LAYERS[@]}"; do just migrate-from-heimathafen "$layer" --dry-run; done
```

Read the lists. Expect three renames in the top layer and two in the others, one repointed
`.groundwork/base`, one `config-key` change per layer file, one `map-preamble` change per `MAP.md`,
and `rewrite` lines for every file that quoted an old name. `would keep` lines are dated records and
anything you excluded: check that every record you care about is there and nothing else is. Add your
own `--exclude` options to this step and to step 4. If a line surprises you, stop and look at that file;
nothing has been written.

### 4. Apply

```sh
cd "$NEW_BASE"
for layer in "${LAYERS[@]}"; do just migrate-from-heimathafen "$layer"; done   # plus any --exclude from step 3
for layer in "${LAYERS[@]}"; do readlink "$layer/.groundwork/base"; done
```

Each `readlink` should name the new base (relatively, from `.groundwork/`). `git -C <layer> status`
shows the changes; there is nothing staged and no new commit.

### 5. Assemble `~/.claude` from the new stack

```sh
cd "$TOP" && just link
```

`link` writes `~/.claude/groundwork/`, then removes the old `~/.claude/hafen/` and the command links
that pointed into the old base. It removes only symlinks into layers it knows, the old `ROOTS` and
the old `INDEX.md`; anything else it reports and keeps.

### 6. Reinstall the hook in every layer

```sh
for layer in "${LAYERS[@]}"; do (cd "$layer" && just install-hooks); done
```

The installed `commit-msg` and its helper are copies. An old copy cannot read the renamed layer file
and would reject a commit the layer's rule allows.

### 7. Check

```sh
for layer in "${LAYERS[@]}"; do (cd "$layer" && echo "== $layer" && just doctor); done
```

Compare the result with `just doctor` before the migration. The mechanism checks should be green in
every layer: `~/.claude symlinks`, `@-imports`, `layer direction`, `maps`, `commit history` and
`hooks`.

### 8. Commit each layer

From each layer, with your own identity (the example reads it from the layer's identity files; use
your own name and email if you keep them elsewhere):

```sh
git add -u && git add groundwork-layer.toml .groundwork    # and, in the top layer, groundwork.toml
git -c user.name="$(cat .groundwork/author-name)" -c user.email="$(cat .groundwork/author-email)" \
    commit --author="$(cat .groundwork/author-name) <$(cat .groundwork/author-email)>" \
    -m "chore(layer): switch to the groundwork names"
```

`git add -u` stages every change to a tracked file, deletions included, and the second command adds
the renamed files, which are new to git. Because the tree was clean before the migration, that is
exactly the migration and nothing else. `git show --stat -M HEAD` shows the renames. Do not push until
step 9 is done.

### 9. Try it

Start a Claude Code session. `/groundwork-self-review` should be listed, `ls ~/.claude/commands`
should show only links into the new base and your layers, and
`rg 'worktree' $(cat ~/.claude/groundwork/ROOTS)` should search every layer. Then push each layer.

### 10. On every other machine

Pull the layers, then run steps 5 and 6 there. Do not run the migration again: the commits already
carry it.

## What `doctor` can still report

The migration itself should add no failure. Two other things show up when `doctor` first runs
against this base, and both are about the notes, not the names:

- **Failures that were already there.** A note without frontmatter, an entry file over its word
  budget, a `vault/companies/` note without `sensitivity`. Compare with the `doctor` run from before
  step 4.
- **Notes that point at files this base no longer has.** The old base held notes (the previous
  issue-tracker adapter and its templates, a few workflow notes) that were dropped or moved when the
  base was made generic. A layer note that names one of them in backticks fails `referenced paths`,
  and a `[[wikilink]]` to it fails `wikilinks`. Decide per reference: repoint it at the file that
  replaced it, copy the old note into your own layer, or drop the reference. That is a content
  decision, so the migration does not make it for you.

## Rollback

The old base is never modified, so going back means restoring the layers and the assembly.

**Before step 8 (nothing committed).** In each layer:

```sh
git reset --hard HEAD && git clean -fd -- groundwork-layer.toml groundwork.toml .groundwork
```

**After step 8, before pushing.** In each layer, with the commit from `heads.txt`:

```sh
git reset --hard <commit-before>
```

**After pushing.** Revert the migration commit instead of rewriting shared history:
`git revert <migration-commit>`. Its subject must conform to the commit rule, for example
`revert(layer): back to the heimathafen names`.

**If a layer's files are damaged in some other way,** replace it with its copy:
`rm -rf <layer> && cp -a "$BACKUP/layer-<n>" <layer>`.

**Then restore the machine** (the old base must still be where the layers' `.hafen/base` pointed):

```sh
cd "$TOP" && just link                         # the old recipes, the old base: rebuilds ~/.claude/hafen
for layer in "${LAYERS[@]}"; do (cd "$layer" && just install-hooks); done
find ~/.claude -maxdepth 2 -type l -lname "$NEW_BASE/*" -print     # links into the new base: review...
find ~/.claude -maxdepth 2 -type l -lname "$NEW_BASE/*" -delete    # ...then remove them
rm -f ~/.claude/groundwork/*-* ~/.claude/groundwork/ROOTS ~/.claude/groundwork/INDEX.md
rmdir ~/.claude/groundwork
cd "$TOP" && just doctor                       # the same result as before the switch
```

`-lname` matches symlinks by their target, and `-delete` removes the link, never the file it points
at. Check that `$NEW_BASE` is an absolute path first: a relative one matches nothing. The hook step
leaves a harmless `gwk.py` in each layer's `.git/hooks/`; `rm` it if you like.
