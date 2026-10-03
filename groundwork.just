# groundwork — task runner for a layer (the base itself, or one stacked on it).
#
# Every layer imports this file, so it is written for repos that commit straight to one branch
# (`workflows/single-branch/commit-discipline.md`): no branch families, no pull requests. What the
# recipes below automate is the rules such a repo has and would otherwise enforce only by
# remembering them: a `commit-msg` hook for type and scope, identity on every commit, never
# `git add -A`, fetch-before-push, the frontmatter convention, and the spec-sheet "never left
# reading like the template" rule.
#
# Requires: just, python3 (3.11 or newer), git.

set shell := ["bash", "-uc"]

groundwork_base := source_directory()
groundwork_layer := justfile_directory()
gwk := "GWK_LAYER=" + quote(groundwork_layer) + " python3 " + quote(groundwork_base) + "/bin/gwk.py"

# Identity is passed on the invocation every time, never read from stored git config
# (`workflows/single-branch/commit-discipline.md`): whoever set a local or global config last
# silently applies to every subsequent commit from anyone using the clone, with no error.
# Set GWK_AUTHOR_NAME and GWK_AUTHOR_EMAIL, or write `.groundwork/author-name` and `.groundwork/author-email` in
# your layer. Those files are per-layer and never ship with the base: an identity is exactly the kind
# of fact the base must not carry. `commit` refuses to run while either is unset. `new-layer` writes
# the two files when GWK_AUTHOR_NAME and GWK_AUTHOR_EMAIL are set while it runs.
author_name := env_var_or_default("GWK_AUTHOR_NAME", `cat .groundwork/author-name 2>/dev/null || echo unset`)
author_email := env_var_or_default("GWK_AUTHOR_EMAIL", `cat .groundwork/author-email 2>/dev/null || echo unset`)

branch := env_var_or_default("GWK_BRANCH", "main")

# List the available recipes
default:
    @just --list

# ------------------------------------------------------------------------------------ hygiene

# Every check this repo can make, in one command
doctor:
    #!/usr/bin/env bash
    set -uo pipefail
    fail=0
    echo "=== frontmatter ===";      {{gwk}} frontmatter || fail=1
    echo "=== wikilinks ===";        {{gwk}} links       || fail=1
    echo "=== referenced paths ==="; {{gwk}} paths       || fail=1
    echo "=== ~/.claude symlinks ==="; {{gwk}} symlinks  || fail=1
    echo "=== @-imports ===";      {{gwk}} imports      || fail=1
    echo "=== layer direction ==="; {{gwk}} direction    || fail=1
    echo "=== maps ===";           {{gwk}} map --check   || fail=1
    echo "=== entry file ===";     {{gwk}} entry        || fail=1
    echo "=== commit history ==="; {{gwk}} check-log      || fail=1
    echo "=== hooks ===";          just hooks-verify     || fail=1
    echo
    if [[ "$fail" -ne 0 ]]; then echo "DOCTOR FAILED"; else echo "all checks clean"; fi
    exit "$fail"

# Check CLAUDE.md is still a router: inside budget, every pointer resolving
entry:
    @{{gwk}} entry

# Regenerate every directory MAP.md from the notes' own frontmatter
map:
    @{{gwk}} map

# Every note under vault/, standards/ and workflows/ carries title and type
lint-frontmatter:
    @{{gwk}} frontmatter

# Every [[wikilink]] resolves to a real note
lint-links:
    @{{gwk}} links

# Every repo-relative path named in backticks still exists
lint-paths:
    @{{gwk}} paths

# Inventory notes carrying real personal/company identity data
sensitive:
    @{{gwk}} sensitive

# Verify ~/.claude's symlinks resolve into this repo, end to end
symlinks:
    @{{gwk}} symlinks

# Install the commit-msg hook into this repo's git dir
install-hooks:
    #!/usr/bin/env bash
    set -euo pipefail
    hooks_dir="$(git rev-parse --git-common-dir)/hooks"
    mkdir -p "$hooks_dir"
    cp {{quote(groundwork_base)}}/bin/commit-msg "$hooks_dir/commit-msg"
    cp {{quote(groundwork_base)}}/bin/gwk.py "$hooks_dir/gwk.py"
    # An earlier name of the script, left behind by a hook installed before the rename.
    rm -f "$hooks_dir/hh.py"
    chmod +x "$hooks_dir/commit-msg"
    echo "installed commit-msg into $hooks_dir"
    echo "Verify it is live rather than assuming — run: just hooks-verify"

# Confirm the installed hook is present, executable and byte-identical to bin/
hooks-verify:
    #!/usr/bin/env bash
    set -euo pipefail
    hooks_dir="$(git rev-parse --git-common-dir)/hooks"
    fail=0
    for f in commit-msg gwk.py; do
      if [[ ! -f "$hooks_dir/$f" ]]; then echo "  MISSING  $f"; fail=1
      elif ! diff -q "$hooks_dir/$f" {{quote(groundwork_base)}}/bin/$f >/dev/null 2>&1; then
        echo "  STALE    $f (run: just install-hooks)"; fail=1
      else echo "  ok       $f"; fi
    done
    exit "$fail"

# Check one candidate subject without committing
check-subject subject:
    @{{gwk}} check-subject "{{subject}}"

# Audit every commit subject in this repo's history
lint-history:
    @{{gwk}} check-log

# ------------------------------------------------------------------------------------ git

# Show what has changed, without touching anything
status:
    @git status --short
    @echo
    @git diff --stat HEAD

# Commit exact paths with explicit identity: just commit docs standards "message" standards/tech/x.md
# Where the layer requires an issue reference, it is taken from a `<family>/<N>-<slug>` branch name
# unless the message already ends in `(#N)`.
commit type scope message +paths:
    #!/usr/bin/env bash
    set -euo pipefail
    # Identity must be real. In a fresh base clone `.groundwork/author-*` does not exist, and the
    # fallback is the literal string "unset" — committing as that is worse than not committing,
    # so refuse rather than produce a commit nobody can attribute.
    if [[ "{{author_name}}" == "unset" || "{{author_email}}" == "unset" ]]; then
        echo "commit: no identity — set GWK_AUTHOR_NAME/GWK_AUTHOR_EMAIL or write .groundwork/author-{name,email}" >&2
        exit 1
    fi
    # Build and check the message before anything is staged, so a rejected message leaves the index
    # alone instead of relying on the next run to clean up after it.
    msg=$({{gwk}} commit-message {{quote(type)}} {{quote(scope)}} {{quote(message)}}) || exit 1
    # Clear the index first. A previously-failed commit leaves its files staged, and the next
    # commit then silently absorbs them — a real incident, where a rejected commit got swallowed
    # into the next one.
    git reset -q

    # just joins a variadic parameter's values with spaces before interpolating, so a filename
    # CONTAINING a space is indistinguishable from two filenames — and a notes repo is full of them
    # ("Reads Merge-Message Templates From the Default Branch....md"). The information is
    # already lost by the time the recipe runs, so disambiguate the only way left: if the whole
    # joined string names something that exists, it is one path, not several.
    #
    # The same family bit another recipe, where a variadic parameter word-split a title into seven
    # arguments. A variadic parameter cannot carry a value with a space in it, full stop.
    # No UNQUOTED expansion anywhere. bash parses both branches before choosing one, so an
    # unquoted `({{paths}})` breaks on a filename containing an apostrophe — "Docker's ..." —
    # even when the other branch would have been taken. `read -a` splits on IFS without
    # evaluating quotes or globs, which is the only safe way to split an interpolated string.
    if [[ -e {{quote(paths)}} ]]; then
      declare -a targets=({{quote(paths)}})
    else
      read -r -a targets <<< {{quote(paths)}}
    fi
    git add -- "${targets[@]}"

    # Assert the staged set is exactly what was asked for. `git add -- <paths>` alone does not
    # guarantee this: it cannot clear something staged before this recipe ran.
    # core.quotePath=false is load-bearing, not tidiness: git escapes any non-ASCII byte in a
    # path ("ICM — Folder..." becomes "ICM \342\200\224 Folder..."), so the assertion below could
    # never match a wanted path containing an em-dash — and a notes repo is full of them. The recipe
    # refused a correct commit rather than allowing a wrong one, which is the right way to fail,
    # but it made every such note uncommittable through the only sanctioned path.
    staged=$(git -c core.quotePath=false diff --cached --name-only | sort)
    want=$(printf '%s\n' "${targets[@]}" | sort)
    if [[ "$staged" != "$want" ]]; then
      echo "ABORT: staged set does not match the paths given" >&2
      echo "  staged:" >&2; echo "$staged" | sed 's/^/    /' >&2
      echo "  wanted:" >&2; echo "$want"   | sed 's/^/    /' >&2
      git reset -q
      exit 1
    fi
    [[ -n "$staged" ]] || { echo "ABORT: nothing staged — did the paths match anything?" >&2; exit 1; }

    # Both -c user.* (the committer) and --author are needed: a commit can silently get the wrong
    # value in either field independently.
    git -c user.name="{{author_name}}" -c user.email="{{author_email}}" \
        commit --author="{{author_name}} <{{author_email}}>" \
        -m "$msg"
    echo
    git log --oneline -1

# Fetch, check for divergence, rebase only if needed, then push and verify it landed
push:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! git remote get-url origin >/dev/null 2>&1; then
      echo "no origin remote — nothing to push"; exit 0
    fi
    git fetch origin {{branch}}
    if ! git diff --quiet HEAD "origin/{{branch}}" -- 2>/dev/null; then
      behind=$(git rev-list --count HEAD..origin/{{branch}})
      if [[ "$behind" -gt 0 ]]; then
        echo "origin/{{branch}} is $behind commit(s) ahead — rebasing before push"
        git rebase "origin/{{branch}}"
      fi
    fi
    git push origin {{branch}}
    # A non-fast-forward failure is not an error to fight; it means something landed first.
    # Verify the remote actually moved rather than trusting the exit code
    # (vault/technical/git/verify-commit-and-push-actually-landed.md).
    local_sha=$(git rev-parse HEAD)
    remote_sha=$(git ls-remote origin "refs/heads/{{branch}}" | cut -f1)
    if [[ "$local_sha" != "$remote_sha" ]]; then
      echo "PUSH DID NOT LAND: local $local_sha != remote $remote_sha" >&2; exit 1
    fi
    echo "pushed and verified: $local_sha"

# ------------------------------------------------------------------------------------ session

# Prepend a session-log entry (newest first)
session-log title summary:
    #!/usr/bin/env bash
    set -euo pipefail
    log="SESSION_LOG.md"
    today=$(date +%Y-%m-%d)
    tmp=$(mktemp)
    # Keep the "# Session Log" header at the top and insert directly beneath it, so entries stay
    # newest-first without the header drifting down the file.
    {
      head -n 1 "$log"
      echo
      printf '## [%s] %s\n' "$today" {{quote(title)}}
      echo
      printf '%s\n' {{quote(summary)}}
      tail -n +2 "$log"
    } > "$tmp"
    mv "$tmp" "$log"
    echo "prepended to $log:"
    sed -n '1,8p' "$log"

# Routine end-of-session housekeeping — reports only, never commits on its own
wrap-up:
    #!/usr/bin/env bash
    set -uo pipefail
    echo "=== working tree ==="
    git status --short || true
    echo
    echo "=== diff stat ==="
    git diff --stat HEAD || true
    echo
    echo "=== checks ==="
    just doctor || true
    echo
    echo "=== unpushed ==="
    if git remote get-url origin >/dev/null 2>&1; then
      git log --oneline "origin/{{branch}}..HEAD" 2>/dev/null || echo "  (could not compare to origin)"
    else
      echo "  no remote"
    fi
    echo
    echo "Next, by hand and in this order:"
    echo "  1. just commit <type> <scope> \"<message>\" <exact paths>   # never git add -A"
    echo "  2. just session-log \"<title>\" \"<summary>\""
    echo "  3. just push"
    echo
    echo "Rename this session:  [$(date +%Y-%m-%d)] <project-or-topic> - <what was done>"

# ------------------------------------------------------------------------------------ projects

# Scaffold a new spec-sheet draft from the master template
new-project slug:
    @{{gwk}} new-project {{slug}}

# Fail while any spec section still reads verbatim from the template
spec-check slug:
    @{{gwk}} spec-check {{slug}}

# Find Claude Code memory files mentioning a scrapped project (reports only, deletes nothing)
retire-project name:
    @{{gwk}} memory-scan {{name}}

# ------------------------------------------------------------------------------------ disk

# Report regenerable dev-tooling cache buildup; removes nothing
disk-report:
    #!/usr/bin/env bash
    set -uo pipefail
    echo "=== Hatch environment cache ==="
    found=0
    for d in "$HOME/Library/Application Support/hatch/env" "$HOME/.local/share/hatch/env"; do
      [[ -d "$d" ]] && { du -sh "$d" 2>/dev/null; found=1; }
    done
    [[ "$found" -eq 1 ]] || echo "  none"
    echo
    # Where your repos live is yours to say: there is no layout the base can assume.
    projects="${GWK_PROJECTS_DIR:-}"
    echo "=== git worktrees under ${projects:-\$GWK_PROJECTS_DIR (not set)} ==="
    if [[ -z "$projects" ]]; then
      echo "  set GWK_PROJECTS_DIR to the directory holding your repos to scan for orphaned worktrees"
    else
      # A worktree goes silently orphaned when its main checkout moves: `git worktree list` run from
      # the new location will not even show it, so these never self-report as stale.
      find "$projects" -name '.git' -maxdepth 5 -type f 2>/dev/null | while read -r f; do
        target=$(sed 's/^gitdir: //' "$f")
        case "$target" in /*) abs="$target";; *) abs="$(dirname "$f")/$target";; esac
        [[ -e "$abs" ]] || echo "  ORPHANED: $(dirname "$f")"
      done
      echo "  (nothing listed above means every worktree link resolves)"
    fi
    echo
    echo "=== container tooling ==="
    command -v podman  >/dev/null && podman machine list 2>/dev/null | head -5 || echo "  no podman"
    command -v limactl >/dev/null && limactl list 2>/dev/null | head -5 || true
    command -v docker  >/dev/null && docker system df 2>/dev/null | head -6 || echo "  no docker"
    echo
    echo "Nothing was removed. Confirm each item before deleting — disk-hygiene.md."

# The pre-publish gate. Stricter than `split-check`: this is the one that must be green before
# this repo is ever pushed to a public remote.
publish-check:
    #!/usr/bin/env bash
    set -uo pipefail
    fail=0
    echo "=== layer direction ==="; {{gwk}} direction   || fail=1
    echo "=== publishable ===";     {{gwk}} publishable || fail=1
    echo
    if [[ "$fail" -ne 0 ]]; then echo "NOT PUBLISHABLE"; else echo "publishable"; fi
    exit "$fail"

# Create an empty layer of your own, stacked on this base: just new-layer ~/my-layer
new-layer path name="":
    @{{gwk}} new-layer {{quote(path)}} {{ if name == "" { "" } else { "--name " + quote(name) } }}

# Rewrite one private layer from the heimathafen names to groundwork's (--dry-run first; never commits).
# `set -f`: a quoted --exclude glob reaches the program as written, the shell does not expand it.
migrate-from-heimathafen layer *flags:
    @set -f; {{gwk}} migrate-from-heimathafen {{quote(layer)}} {{flags}}

# Run the mechanism's own unit tests
gwk-test:
    python3 -m unittest discover -s {{quote(groundwork_base)}}/tests -v

# Assemble ~/.claude from the layer stack: the groundwork/ handles, ROOTS, INDEX.md, the entry-file
# symlink, and the merged commands/skills/agents. Idempotent — re-run after any layer moves.
link:
    @{{gwk}} link
