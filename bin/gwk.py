#!/usr/bin/env python3
"""Checks and scaffolding for groundwork's own conventions.

Called from the justfile recipes (`groundwork.just`), not by hand. Stdlib only, no packaging: this is a
notes repo, and a `pyproject.toml` here would be ceremony around a handful of checks. Needs
Python 3.11 or newer (`tomllib`).

What it enforces is not invented: the frontmatter convention, the commit rule and the layer
direction rule are each conventions that real content already follows, and a rule that real
content already follows is worth a gate, because the next drift is then visible instead of
ordinary.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import tomllib

#: Where the mechanism lives — the repo containing this file. Under one repo this was the same
#: thing as "what is being checked"; under a stack of layers it never is again. Keeping them
#: separate is what lets one copy of `gwk.py`, shipped from the public base, check any layer.
BASE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAYER_FILE = "groundwork-layer.toml"
STACK_FILE = "groundwork.toml"
STATE_DIR = ".groundwork"
RECIPES_FILE = "groundwork.just"

#: The names this mechanism had before it was called groundwork. Only the names of the mechanism
#: are listed here: a layer's own notes, its repository name and the German word "Hafen" are none
#: of this command's business.
LEGACY_LAYER_FILE = "hafen-layer.toml"
LEGACY_STACK_FILE = "hafen.toml"
LEGACY_STATE_DIR = ".hafen"
LEGACY_RECIPES_FILE = "hafen.just"
LEGACY_ASSEMBLY = "hafen"

#: The base layer's identity, in one place. The slash commands and the entry file of a stack import
#: the base through its handle (`~/.claude/groundwork/00-base/…`), and a handle is `<rank>-<name>`, so
#: the base must be declared with exactly this name and rank in the top layer's `groundwork.toml`.
#: `new-layer` writes it that way, and `link` fails with a message when a stack does not.
BASE_NAME = "base"
BASE_RANK = 0


def layer_handle(layer: dict) -> str:
    """The directory name `link` gives a layer under `~/.claude/groundwork/`."""
    return f"{layer['rank']:02d}-{layer['name']}"


BASE_HANDLE = layer_handle({"rank": BASE_RANK, "name": BASE_NAME})


def _git_toplevel() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out or None


def resolve_layer(explicit: str | None = None) -> str:
    """Which layer is being checked. Explicit flag, then env, then cwd's repo, then this repo.

    The justfile sets $GWK_LAYER on every invocation, so cwd-sensitivity never decides anything
    in normal use. The git fallback is for hand invocation, which the module docstring says should
    not happen anyway.
    """
    for candidate in (explicit, os.environ.get("GWK_LAYER"), _git_toplevel()):
        if candidate and os.path.isfile(os.path.join(candidate, LAYER_FILE)):
            return os.path.abspath(candidate)
    return BASE_ROOT


def layer_config(root: str) -> dict:
    path = os.path.join(root, LAYER_FILE)
    if not os.path.isfile(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def resolve_stack(root: str) -> list[dict]:
    """The ordered layer stack, lowest rank first.

    A layer with no `groundwork.toml` is its own single-layer stack. That is not a degraded mode — it is
    how a base-only clone works, and every command has to stay green in it or the base is not
    actually standalone.
    """
    manifest = os.path.join(root, STACK_FILE)
    if not os.path.isfile(manifest):
        cfg = layer_config(root)
        me = {"name": cfg.get("name", os.path.basename(root)), "root": root, "rank": 0}
        # Only the top layer owns a `groundwork.toml`. A middle layer still has to resolve its own
        # legitimate downward references, and `.groundwork/base` already declares the layer beneath it —
        # so walk that link rather than making every layer restate the stack.
        below = os.path.join(root, ".groundwork", "base")
        if os.path.isdir(below):
            stack = resolve_stack(os.path.realpath(below))
            me["rank"] = (stack[-1]["rank"] if stack else 0) + 10
            return stack + [me]
        return [me]

    with open(manifest, "rb") as f:
        data = tomllib.load(f)

    layers = []
    for entry in data.get("layer", []):
        # realpath, not abspath: a layer reached through a `.groundwork/base` symlink would otherwise
        # be recorded at a path that only exists while the layer holding that symlink does.
        resolved = os.path.realpath(os.path.join(root, entry["path"]))
        layers.append({"name": entry["name"], "root": resolved, "rank": int(entry["rank"])})
    layers.sort(key=lambda x: x["rank"])
    return layers


ROOT = resolve_layer()
CONFIG = layer_config(ROOT)
NOTE_DIRS = tuple(CONFIG.get("note_dirs", ("vault", "standards", "workflows")))

REQUIRED_FIELDS = ("title", "type")   # vault/README.md: "at minimum title and type"
EXPECTED_FIELDS = ("category",)       # near-universal; a miss is a warning, not a failure
SENSITIVE_DIR = "vault/companies/"    # every note here must declare its `sensitivity`

WIKILINK = re.compile(r"\[\[([^\]|#]+)")

# Commit-message rule: `type(scope): description`, scope required, plus a trailing issue reference
# `(#N)` unless the layer says it has no tracker (`commit_reference = "none"` in `groundwork-layer.toml`,
# or GWK_COMMIT_REFERENCE in the environment). That is the only difference between the two rules,
# and it follows from the repo's shape rather than being a relaxation of discipline.
#
# No merge exemption (workflows/repo-workflow/commits-and-prs.md). That costs nothing in a
# single-branch repo: `just push` rebases onto origin rather than merging, so such a repo does not
# generate merge commits in normal use.
REFERENCE_STYLES = ("issue", "none")
DEFAULT_REFERENCE = "issue"

#: The twelve types of `workflows/repo-workflow/commits-and-prs.md`. A word outside this list is
#: rejected, not waved through: `wip(x): ...` conforms to the shape and to nothing else.
COMMIT_TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore",
                "revert", "merge", "release")
_SUBJECT_HEAD = r"^(?:" + "|".join(COMMIT_TYPES) + r")\([a-z0-9_-]+\)!?: "
COMMIT_SUBJECT = {
    "issue": re.compile(_SUBJECT_HEAD + r".+ \(#\d+\)$"),
    "none": re.compile(_SUBJECT_HEAD + r".+$"),
}
COMMIT_BASELINE = ".groundwork/commit-baseline.txt"

# Fenced blocks and inline code spans are stripped before any link or path scan. A TOML
# array-of-table header (`[[layer]]`, `[[package]]`) is lexically identical to a wikilink, and a
# notes repo that documents TOML formats will quote them — scanning raw text reports every such
# header as a broken link.
FENCED = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`]{0,200}`", re.DOTALL)


def strip_code(raw: str) -> str:
    return INLINE_CODE.sub(" ", FENCED.sub(" ", raw))

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = YELLOW = DIM = RESET = ""


# ------------------------------------------------------------------------------------- utilities


def notes(dirs: tuple[str, ...] = NOTE_DIRS) -> list[str]:
    out = []
    for d in dirs:
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, d)):
            dirnames[:] = [x for x in dirnames if x not in {".git", "graphify-out", "__pycache__"}]
            out.extend(
                os.path.join(dirpath, f) for f in filenames if f.endswith(".md")
            )
    return sorted(out)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT)


def layer_roots() -> list[str]:
    """Every layer root in the stack, lowest rank first."""
    return [L["root"] for L in resolve_stack(ROOT)]


def stack_notes() -> list[str]:
    """Every note across every layer, each layer contributing its own declared `note_dirs`.

    Cross-layer resolution is the point of a stack: a personal note citing a base note is correct,
    and checking each layer in isolation would report every such reference as broken. The direction
    rule (`gwk direction`) is what keeps this from becoming a licence to reference upward.
    """
    out = []
    for root in layer_roots():
        dirs = tuple(layer_config(root).get("note_dirs", NOTE_DIRS))
        for d in dirs:
            base = os.path.join(root, d)
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [x for x in dirnames
                               if x not in {".git", "graphify-out", "__pycache__"}]
                out.extend(os.path.join(dirpath, f)
                           for f in filenames if f.endswith(".md"))
    return sorted(set(out))


def resolves_in_stack(target: str) -> bool:
    """Does a repo-relative path exist in ANY layer of the stack?"""
    return any(os.path.exists(os.path.join(root, target)) for root in layer_roots())


def read(path: str) -> str:
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def _scalar(raw: str) -> str:
    """Unquote one frontmatter value, honouring escapes.

    A plain `strip('"')` leaves an inner `\\"` escaped and truncates a title at a quote, so a map
    generated with it differs from one generated by any parser that honours escapes, and whichever
    ran last would make the other's `map --check` go red.
    """
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        inner = raw[1:-1]
        if raw[0] == '"':
            return inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner.replace("''", "'")
    return raw


def frontmatter(raw: str) -> dict[str, str]:
    """Parse the flat scalar frontmatter this repo uses. Degrades to {} rather than raising."""
    if not raw.startswith("---"):
        return {}
    try:
        end = raw.index("\n---\n", 3)
    except ValueError:
        return {}
    data: dict[str, str] = {}
    for line in raw[raw.index("\n") + 1 : end].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if sep and not key.startswith(" "):
            data[key.strip()] = _scalar(value)
    return data


def report(label: str, problems: list[str], warnings: list[str] | None = None) -> int:
    for w in warnings or []:
        print(f"  {YELLOW}warn{RESET}  {w}")
    for p in problems:
        print(f"  {RED}FAIL{RESET}  {p}")
    if problems:
        print(f"  {RED}{label}: {len(problems)} problem(s){RESET}")
        return 1
    print(f"  {GREEN}ok{RESET}    {label}")
    return 0


# ------------------------------------------------------------------------------- dated records

#: A dated record says what was true on its date: a session log, an audit, a ruling. Its old
#: wording is the record, so a rename must not rewrite it and a file that has since moved must not
#: make it fail. The default test is the name alone: `SESSION_LOG.md`, or a markdown file whose name
#: carries `-YYYY-MM-DD` (`audit-2026-10-03.md`, `rulings-2026-09-20.md`). A date set off by a
#: space ("Capability Matrix 2026-08-12.md") is a "facts as of" note that is kept current, not a
#: record, and is not matched. Month and day are validated, so `-2026-13-45` is not a date.
DATED_RECORD_NAME = re.compile(r"-(?:19|20)\d\d-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])(?!\d).*\.md$")
DATED_RECORD_FILES = ("SESSION_LOG.md",)


def is_dated_record(relative: str) -> bool:
    """Is this repo-relative path a dated record by the built-in name rule?"""
    name = os.path.basename(relative)
    return name in DATED_RECORD_FILES or DATED_RECORD_NAME.search(name) is not None


def note_history(kind: str, history: dict[str, int]) -> None:
    """Say, without failing, which dated records cite things that no longer exist."""
    if history:
        total = sum(history.values())
        print(f"  {DIM}{total} {kind}(s) in {len(history)} dated record(s) kept as history "
              f"(they say what was true on their date): {', '.join(sorted(history))}{RESET}")




# ------------------------------------------------------------------------------- the entry file

#: Budget for `claude/CLAUDE.md`. It is loaded into every session, so every word costs on every
#: request — and it grew to 1,508 words by accumulating one reasonable-looking line at a time. No
#: single addition was wrong; the sum was. A number is the only thing that catches a sum.
ENTRY_FILE = CONFIG.get("entry_file", "claude/CLAUDE.md")
ENTRY_MAX_WORDS = int(CONFIG.get("entry_max_words", 900))

#: Bare filenames that legitimately appear without a directory.
ENTRY_BARE_OK = {"README.md", "CLAUDE.md", "MAP.md", "SKILL.md", "SESSION_LOG.md", "AGENTS.md",
                 # assembled/manifest artifacts, which live outside any layer directory
                 "groundwork.toml", "groundwork-layer.toml", "ROOTS", "INDEX.md"}

ENTRY_PATH = re.compile(r"`([A-Za-z0-9_~][A-Za-z0-9_./~-]*\.md|[A-Za-z0-9_][A-Za-z0-9_./-]*/)`")


def cmd_entry(_args) -> int:
    """The entry file must stay a router: inside its budget, and pointing at things that exist.

    A router with a dead pointer is worse than no router — the reader follows it, finds nothing, and
    concludes the subject does not exist. Two were written into this file on 2026-08-30 within an
    hour of it being rewritten, and a script caught both.
    """
    entry_path = os.path.join(ROOT, ENTRY_FILE)
    if not os.path.isfile(entry_path):
        # Not every layer contributes a router. A layer that adds only notes has nothing to route,
        # and the assembler picks the highest-ranked layer that does provide one.
        print(f"  {DIM}no {ENTRY_FILE} in this layer — nothing to check{RESET}")
        return 0
    raw = read(entry_path)
    problems, warnings = [], []

    words = len(raw.split())
    if words > ENTRY_MAX_WORDS:
        problems.append(
            f"{ENTRY_FILE} is {words} words, over the {ENTRY_MAX_WORDS}-word budget — "
            f"move detail into a note and link it, do not raise this number"
        )
    elif words > ENTRY_MAX_WORDS * 0.9:
        warnings.append(f"{ENTRY_FILE} is {words} words, close to the {ENTRY_MAX_WORDS} budget")

    for named in ENTRY_PATH.findall(raw):
        if named.startswith("~"):
            continue  # an absolute path to this repo, resolved by the reader's own home
        if named in ENTRY_BARE_OK:
            continue
        if "/" not in named:
            problems.append(f"{ENTRY_FILE} names {named!r} with no directory — it cannot be found")
        elif not resolves_in_stack(named):
            problems.append(f"{ENTRY_FILE} points at {named}, which does not exist")

    return report(f"entry file ({words} words)", problems, warnings)


# ------------------------------------------------------------------------------------------- map

# What each mapped directory is for. This used to be a dict literal here, on the reasoning that it
# "describes the *structure*, and the structure is what the generator's subject is — stated once,
# reviewed as code." That reasoning held under one repo and breaks under three: the base's copy of
# this generator must not name `vault/`, because the base must not contain one. So it moved to each
# layer's own `groundwork-layer.toml`, which keeps the "stated once" property while letting the layer
# that owns a directory be the thing that describes it.
def map_dirs(root: str = None) -> dict[str, tuple[str, str]]:
    cfg = CONFIG if root in (None, ROOT) else layer_config(root)
    return {
        name: (table["heading"], table["purpose"])
        for name, table in cfg.get("map", {}).items()
    }


MAP_DIRS = map_dirs()

MAP_NAME = "MAP.md"

MAP_PREAMBLE = """<!-- GENERATED by `just map` from each note's frontmatter — never hand-edit.
     `just doctor` fails when this file no longer matches the tree.
     To change an entry, change that note's `title:`. To add one, add the note. -->"""


def map_notes(top: str) -> list[str]:
    """Every mapped note under one top-level directory, excluding the map itself."""
    out = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, top)):
        dirnames[:] = [d for d in dirnames if d not in {".git", "graphify-out", "__pycache__"}]
        for name in filenames:
            if name.endswith(".md") and name != MAP_NAME:
                out.append(os.path.join(dirpath, name))
    return sorted(out)


def map_title(path: str) -> str:
    """A note's one-line identity: its frontmatter title, else its first heading, else its name.

    Never invented here. A title that reads badly in a map reads badly in the note too, and the
    fix belongs in the note — one home per fact.
    """
    raw = read(path)
    title = frontmatter(raw).get("title", "").strip()
    if title:
        return title
    for line in raw.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return os.path.basename(path)[:-3]


def render_map(top: str) -> str:
    heading, purpose = MAP_DIRS[top]
    paths = map_notes(top)

    groups: dict[str, list[str]] = {}
    for path in paths:
        relative = os.path.relpath(path, os.path.join(ROOT, top))
        section = os.path.dirname(relative) or "."
        groups.setdefault(section, []).append(relative)

    lines = [
        "---",
        f'title: "Map — {top}"',
        'type: "index"',
        'category: "map"',
        "---",
        "",
        MAP_PREAMBLE,
        "",
        f"# {heading}",
        "",
        purpose,
        "",
        f"{len(paths)} notes. Paths are relative to `{top}/`.",
        "",
    ]

    for section in sorted(groups):
        lines.append(f"## {section}" if section != "." else f"## {top}/")
        lines.append("")
        for relative in groups[section]:
            title = map_title(os.path.join(ROOT, top, relative))
            # URL-encode only the space: these filenames are full of them, and a raw space
            # breaks the link target in every renderer while leaving the text looking correct.
            lines.append(f"- [{title}]({relative.replace(' ', '%20')})")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def cmd_map(args) -> int:
    """Write each directory's map, or verify the committed ones still match the tree."""
    problems, wrote = [], []
    for top in MAP_DIRS:
        destination = os.path.join(ROOT, top, MAP_NAME)
        fresh = render_map(top)
        current = read(destination) if os.path.exists(destination) else None

        if getattr(args, "check", False):
            if current is None:
                problems.append(f"{top}/{MAP_NAME} is missing — run: just map")
            elif current != fresh:
                problems.append(f"{top}/{MAP_NAME} is stale — run: just map")
            continue

        if not os.path.isdir(os.path.dirname(destination)):
            problems.append(f"{top}/ is declared in {LAYER_FILE} but the directory does not exist — "
                            f"create it, or remove [map.{top}]")
            continue
        if current != fresh:
            with open(destination, "w", encoding="utf-8", newline="") as f:
                f.write(fresh)
            wrote.append(f"{top}/{MAP_NAME}")

    if getattr(args, "check", False):
        return report("maps match the tree", problems)

    for name in wrote:
        print(f"  {GREEN}wrote{RESET} {name}")
    if problems:
        return report("maps", problems)
    if not wrote:
        print(f"  {DIM}no change — every map already matches the tree{RESET}")
    return 0


# ---------------------------------------------------------------------------------------- checks


def cmd_frontmatter(_args) -> int:
    problems, warnings = [], []
    for path in notes():
        fm = frontmatter(read(path))
        if not fm:
            problems.append(f"{rel(path)}: no parseable frontmatter")
            continue
        for field in REQUIRED_FIELDS:
            if not fm.get(field):
                problems.append(f"{rel(path)}: missing required '{field}'")
        for field in EXPECTED_FIELDS:
            if not fm.get(field):
                warnings.append(f"{rel(path)}: missing '{field}'")
        # A note about a real entity must say so in its own frontmatter. The convention existed and
        # was advertised as greppable, but only one note in the tree actually carried the field
        # while the note holding five public IPs and four order numbers carried none. A convention
        # nothing enforces is a label, not a guardrail.
        if rel(path).startswith(SENSITIVE_DIR) and not fm.get("sensitivity"):
            problems.append(f"{rel(path)}: under {SENSITIVE_DIR} but has no 'sensitivity' field")
    return report(f"frontmatter ({len(notes())} notes)", problems, warnings)


def _link_index() -> dict[str, str]:
    """Map every resolvable link target -> the file providing it (filename stem and title)."""
    index: dict[str, str] = {}
    for path in stack_notes():
        stem = os.path.splitext(os.path.basename(path))[0]
        index.setdefault(stem.lower(), path)
        title = frontmatter(read(path)).get("title")
        if title:
            index.setdefault(title.lower(), path)
    return index


BASELINE = ".groundwork/link-baseline.txt"


def _baseline() -> set[str]:
    """Link targets already known dangling when this check was introduced.

    These are references to notes the groundwork migration deliberately did not carry over — the
    old vault's per-repo index notes, its `Home`, its `Departments/` tree. Baselining them is not
    the same as hiding them: the file is explicit, version-controlled, listed by `just lint-links`
    with a count, and anything *new* still fails. A check that is permanently red gets ignored,
    which is the same as having no check.

    Shrinking this file is a real cleanup task, not a background chore — decide per link whether
    the note should be written, the link rewritten, or the reference dropped.
    """
    path = os.path.join(ROOT, BASELINE)
    if not os.path.isfile(path):
        return set()
    return {
        line.strip()
        for line in read(path).split("\n")
        if line.strip() and not line.startswith("#")
    }


def cmd_links(_args) -> int:
    index = _link_index()
    baseline = _baseline()
    known = 0
    history: dict[str, int] = {}
    problems = []
    for path in notes():
        for target in WIKILINK.findall(strip_code(read(path))):
            target = " ".join(target.split())
            if not target:
                continue
            basename = target.rsplit("/", 1)[-1]
            if target.lower() in index or basename.lower() in index:
                continue
            if target in baseline:
                known += 1
                continue
            if is_dated_record(rel(path)):
                history[rel(path)] = history.get(rel(path), 0) + 1
                continue
            problems.append(f"{rel(path)}: [[{target}]] resolves to nothing")
    note_history("dangling wikilink", history)
    if known:
        print(f"  {DIM}{known} known-dangling link(s) from the vault migration, "
              f"baselined in {BASELINE}{RESET}")
    return report("wikilinks", problems)


def cmd_paths(_args) -> int:
    """Repo-relative paths named in backticks that no longer exist.

    Catches the drift class that keeps recurring here: a doc naming a file that was moved or
    deleted, e.g. `CLAUDE.md` pointing at `workflows/tools/helper.py` after that script is
    retired. Only checked for paths that look repo-relative and carry a real extension, so ordinary
    prose in backticks is not dragged in.
    """
    tops = {"claude"}
    for root in layer_roots():
        tops.update(layer_config(root).get("note_dirs", NOTE_DIRS))
    candidate = re.compile(r"`((?:" + "|".join(sorted(tops)) + r")/[\w./-]+\.\w+)`")
    problems = []
    history: dict[str, int] = {}
    for path in notes() + [os.path.join(ROOT, "README.md"), os.path.join(ROOT, "claude/CLAUDE.md")]:
        if not os.path.isfile(path):
            continue
        for target in set(candidate.findall(read(path))):
            if not resolves_in_stack(target):
                if is_dated_record(rel(path)):
                    history[rel(path)] = history.get(rel(path), 0) + 1
                    continue
                problems.append(f"{rel(path)}: `{target}` does not exist in any layer")
    note_history("dead path reference", history)
    return report("referenced paths", problems)


def cmd_sensitive(_args) -> int:
    hits = [rel(p) for p in notes() if 'sensitivity: "real-identity"' in read(p)]
    print(f"  {len(hits)} note(s) carrying real identity data — never usable as example/seed data:")
    for h in hits:
        print(f"    {h}")
    return 0


def cmd_symlinks(_args) -> int:
    """Verify the assembled ~/.claude matches the manifest, end to end.

    Keeps the principle the single-repo version was built on — enumerate what is actually there
    rather than trusting a hardcoded list — and extends it to the merged layout: `CLAUDE.md` is a
    symlink into some layer, `commands/`/`skills/`/`agents/` are real directories whose every entry
    is a symlink into some layer, and `groundwork/` matches the manifest exactly. An extra stale handle
    is a failure, not a shrug: it means a layer was removed and nothing noticed.
    """
    if not CONFIG.get("assembled", True):
        print(f"  {DIM}not the assembled layer (assembled = false) — nothing to verify{RESET}")
        return 0

    stack = resolve_stack(ROOT)
    roots = [L["root"] for L in stack]
    problems = []

    def into_layer(target: str) -> bool:
        return any(target == r or target.startswith(r + os.sep) for r in roots)

    entry = os.path.join(CLAUDE_DIR, "CLAUDE.md")
    if not os.path.islink(entry):
        problems.append("~/.claude/CLAUDE.md is not a symlink")
    elif not os.path.exists(entry):
        problems.append(f"~/.claude/CLAUDE.md -> {os.readlink(entry)} (DANGLING)")
    elif not into_layer(_declared_target(entry)):
        problems.append("~/.claude/CLAUDE.md points outside every declared layer")
    else:
        print(f"  {DIM}~/.claude/CLAUDE.md -> {_declared_target(entry)}{RESET}")

    # settings.json is optional: only a stack that provides one owes a link. Claude Code rewrites it
    # on /config changes, and a writer that replaces the file instead of writing through the link
    # turns it back into a real file; that is exactly what this catches.
    settings = os.path.join(CLAUDE_DIR, "settings.json")
    if any(os.path.isfile(os.path.join(L["root"], SETTINGS_FILE)) for L in stack):
        if not os.path.islink(settings):
            problems.append("~/.claude/settings.json is not a symlink — move changes into the "
                            "layer's claude/settings.json, then: just link")
        elif not os.path.exists(settings):
            problems.append(f"~/.claude/settings.json -> {os.readlink(settings)} (DANGLING)")
        elif not into_layer(_declared_target(settings)):
            problems.append("~/.claude/settings.json points outside every declared layer")
        else:
            print(f"  {DIM}~/.claude/settings.json -> {_declared_target(settings)}{RESET}")

    for kind in MERGE_FILES + MERGE_DIRS:
        full = os.path.join(CLAUDE_DIR, kind)
        if os.path.islink(full) or not os.path.isdir(full):
            problems.append(f"~/.claude/{kind} is not a real directory — run: just link")
            continue
        entries = sorted(os.listdir(full))
        for name in entries:
            item = os.path.join(full, name)
            if not os.path.islink(item):
                continue                          # a stranger; `link` reports these, not an error
            if not os.path.exists(item):
                problems.append(f"~/.claude/{kind}/{name} is DANGLING")
            elif not into_layer(_declared_target(item)):
                problems.append(f"~/.claude/{kind}/{name} points outside every declared layer")
        print(f"  {DIM}~/.claude/{kind}/ — {len(entries)} entr(y/ies){RESET}")

    # A declared layer whose directory is gone is the failure this whole check exists for: the
    # handles still point at the old path, and `realpath` happily computes a path for something
    # that no longer exists, so comparing targets alone reports a clean bill of health.
    for layer in stack:
        if not os.path.isdir(layer["root"]):
            problems.append(f"layer {layer['name']!r} is declared but its directory is gone: "
                            f"{layer['root']}")

    expected = {layer_handle(L): L["root"] for L in stack}
    if not os.path.isdir(GROUNDWORK_DIR):
        problems.append("~/.claude/groundwork/ is missing — run: just link")
    else:
        found = {n for n in os.listdir(GROUNDWORK_DIR) if os.path.islink(os.path.join(GROUNDWORK_DIR, n))}
        for name in sorted(found - set(expected)):
            problems.append(f"~/.claude/groundwork/{name} is not in the manifest (stale layer?)")
        for name, root in sorted(expected.items()):
            link = os.path.join(GROUNDWORK_DIR, name)
            if name not in found:
                problems.append(f"~/.claude/groundwork/{name} is missing — run: just link")
            elif _declared_target(link) != root:
                problems.append(f"~/.claude/groundwork/{name} points at the wrong layer")
        roots_file = os.path.join(GROUNDWORK_DIR, "ROOTS")
        if not os.path.isfile(roots_file):
            problems.append("~/.claude/groundwork/ROOTS is missing — run: just link")
        elif [x for x in read(roots_file).split("\n") if x] != roots:
            problems.append("~/.claude/groundwork/ROOTS does not match the manifest — run: just link")
        if not os.path.isfile(os.path.join(GROUNDWORK_DIR, "INDEX.md")):
            problems.append("~/.claude/groundwork/INDEX.md is missing — run: just link")

    return report(f"assembled ~/.claude ({len(stack)} layers)", problems)


# --------------------------------------------------------------------------------- commit messages


def commit_reference() -> str:
    """How this layer's commit subjects reference their issue: `issue` (required) or `none`.

    Environment first, then the layer's `groundwork-layer.toml`, then the default. An unknown value is a
    hard error rather than a silent fallback: a typo in `commit_reference` must not quietly turn the
    reference requirement off.
    """
    style = os.environ.get("GWK_COMMIT_REFERENCE") or CONFIG.get("commit_reference", DEFAULT_REFERENCE)
    if style not in REFERENCE_STYLES:
        raise SystemExit(f"commit_reference must be one of {', '.join(REFERENCE_STYLES)} — got {style!r}")
    return style


def commit_expected(reference: str) -> str:
    """The form a conforming subject takes, for error messages."""
    return "type(scope): description (#N)" if reference == "issue" else "type(scope): description"


def check_commit_subject(subject: str, reference: str | None = None) -> str | None:
    """Error message if `subject` does not conform, else None."""
    reference = reference or commit_reference()
    if not subject.strip():
        return "empty subject"
    if COMMIT_SUBJECT[reference].match(subject):
        return None
    leading = re.match(r"^([A-Za-z]+)(?:\([^)]*\))?!?: ", subject)
    if leading and leading.group(1) not in COMMIT_TYPES:
        return (f"unknown type {leading.group(1)!r} — use one of {' '.join(COMMIT_TYPES)}")
    if re.match(r"^[a-z]+!?: ", subject):
        return "scope is required, not optional — got 'type: description' with no (scope)"
    if reference == "issue" and COMMIT_SUBJECT["none"].match(subject):
        return "issue reference is required — end the subject with (#N)"
    return f"does not match '{commit_expected(reference)}'"


def _commit_baseline() -> set[str]:
    path = os.path.join(ROOT, COMMIT_BASELINE)
    if not os.path.isfile(path):
        return set()
    return {
        line.split()[0]
        for line in read(path).split("\n")
        if line.strip() and not line.startswith("#")
    }


def commit_hint(reference: str) -> list[str]:
    """The lines after `got:` in a rejection, shared by `check-subject` and the hook."""
    types = f"types:    {' '.join(COMMIT_TYPES)}"
    if reference == "issue":
        return ["expected: type(scope): description (#N)",
                "          e.g. fix(parser): handle an empty input file (#42)",
                types]
    return ["expected: type(scope): description",
            "          e.g. fix(parser): handle an empty input file",
            types,
            "No trailing issue reference is required here (commit_reference = \"none\")."]


BRANCH_ISSUE = re.compile(r"^[a-z]+/(\d+)(?:-|$)")


def build_commit_message(type_: str, scope: str, message: str, branch: str | None) -> str:
    """`type(scope): message`, plus the issue reference when this layer requires one.

    In `issue` mode a subject that does not already end in `(#N)` gets it from the branch name,
    which the repo workflow spells `<family>/<N>-<slug>` (`workflows/repo-workflow/branch-model.md`).
    A branch that carries no number leaves the subject as it is, so the checker then rejects it
    with its usual "issue reference is required" instead of this helper guessing a number. Only the
    first line is a subject: a body below it is passed through untouched.
    """
    first, newline, body = message.partition("\n")
    subject = f"{type_}({scope}): {first}"
    if commit_reference() == "issue" and not re.search(r" \(#\d+\)$", subject):
        found = BRANCH_ISSUE.match(branch or "")
        if found:
            subject += f" (#{found.group(1)})"
    return subject + newline + body


def cmd_commit_message(args) -> int:
    """Print the full commit message for `just commit`, or reject it before anything is staged."""
    head = subprocess.run(["git", "-C", ROOT, "symbolic-ref", "--short", "-q", "HEAD"],
                          capture_output=True, text=True)
    branch = head.stdout.strip() if head.returncode == 0 else None
    full = build_commit_message(args.type, args.scope, args.message, branch)
    subject = full.partition("\n")[0]
    problem = check_commit_subject(subject)
    if problem:
        print(f"commit: rejected — {problem}", file=sys.stderr)
        print(f"  got:      {subject}", file=sys.stderr)
        for line in commit_hint(commit_reference()):
            print(f"  {line}", file=sys.stderr)
        return 1
    sys.stdout.write(full)
    return 0


def cmd_check_subject(args) -> int:
    problem = check_commit_subject(args.subject)
    if problem:
        print(f"  {RED}commit-msg: rejected — {problem}{RESET}", file=sys.stderr)
        print(f"    got:      {args.subject}", file=sys.stderr)
        for line in commit_hint(commit_reference()):
            print(f"    {line}", file=sys.stderr)
        return 1
    print(f"  {GREEN}ok{RESET}    conforms")
    return 0


def cmd_check_log(_args) -> int:
    """Audit the whole history through the same checker the hook uses."""
    baseline = _commit_baseline()
    done = subprocess.run(
        ["git", "-C", ROOT, "log", "--format=%H %s"],
        capture_output=True, text=True,
    )
    if done.returncode != 0:
        # Two different situations produce a non-zero exit, and neither is a crash: a directory
        # that is not a repository, and a repository with no commits yet (every new layer starts
        # there). The second is not a failure at all — there is nothing to audit.
        inside = subprocess.run(["git", "-C", ROOT, "rev-parse", "--git-dir"],
                                capture_output=True, text=True)
        if inside.returncode != 0:
            print(f"  {RED}FAIL{RESET}  {ROOT} is not a git repository — run: git init")
            return 1
        print(f"  {DIM}no commits yet — nothing to audit{RESET}")
        return 0
    out = done.stdout
    total = conforming = legacy = 0
    offenders = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        sha, _, subject = line.partition(" ")
        total += 1
        if sha in baseline:
            legacy += 1
        elif check_commit_subject(subject) is None:
            conforming += 1
        else:
            offenders.append((sha[:9], subject, check_commit_subject(subject)))
    print(f"  total:         {total}")
    print(f"  conforming:    {conforming}")
    print(f"  grandfathered: {legacy}   (pre-rule; shared history is never rewritten)")
    print(f"  violations:    {len(offenders)}")
    for sha, subject, problem in offenders:
        print(f"    {RED}{sha}{RESET}  {subject[:70]}")
        print(f"               -> {problem}")
    if conforming + legacy + len(offenders) != total:
        print("  WARNING: buckets do not sum to the total", file=sys.stderr)
        return 1
    return 1 if offenders else 0


# ------------------------------------------------------------------------------- spec sheet flow

TEMPLATE = "workflows/session/templates/enterprise-spec-sheet-template.md"


def _sections(raw: str) -> dict[str, str]:
    out, current, buf = {}, None, []
    for line in raw.split("\n"):
        if line.startswith("#"):
            if current:
                out[current] = "\n".join(buf).strip()
            current, buf = line.strip(), []
        elif current:
            buf.append(line)
    if current:
        out[current] = "\n".join(buf).strip()
    return out


def cmd_spec_check(args) -> int:
    """Flag spec-sheet sections still reading like the template's own generic prompt text.

    `start-new-project.md` step 1a requires iterating "until every section is filled with real
    project-specific content or explicitly marked out of scope, never left reading like the
    template's own generic prompt text". That is a real rule with no mechanism — this is the
    mechanism. Rather than guessing at placeholder tokens, it diffs the draft against the template
    section by section: an untouched section is one whose body is still byte-identical.
    """
    draft = os.path.join(ROOT, "vault/projects", args.slug, "spec.md")
    if not os.path.isfile(draft):
        print(f"  {RED}no spec at {rel(draft)}{RESET}")
        return 1

    template_sections = _sections(read(os.path.join(ROOT, TEMPLATE)))
    draft_sections = _sections(read(draft))

    untouched, missing = [], []
    for heading, body in template_sections.items():
        if heading not in draft_sections:
            missing.append(heading)
        elif body and draft_sections[heading] == body:
            untouched.append(heading)

    for heading in missing:
        print(f"  {YELLOW}warn{RESET}  section absent from the draft: {heading}")
    problems = [f"still verbatim from the template: {h}" for h in untouched]
    return report(f"spec-check {args.slug}", problems)


def cmd_new_project(args) -> int:
    target_dir = os.path.join(ROOT, "vault/projects", args.slug)
    target = os.path.join(target_dir, "spec.md")
    if os.path.exists(target):
        print(f"  {RED}refusing to overwrite {rel(target)}{RESET}")
        return 1
    os.makedirs(target_dir, exist_ok=True)

    raw = read(os.path.join(ROOT, TEMPLATE))
    body = raw[raw.index("\n---\n", 3) + len("\n---\n") :]
    header = (
        "---\n"
        f'title: "{args.slug} — specification sheet"\n'
        'type: "spec"\n'
        'category: "projects"\n'
        f'repo: "{args.slug}"\n'
        "---\n"
    )
    with open(target, "w", encoding="utf-8", newline="") as f:
        f.write(header + body)
    print(f"  created {rel(target)}")
    print(f"  {DIM}Iterate section by section with the maintainer; nothing starts until spec-check passes.{RESET}")
    return 0


# ------------------------------------------------------------------------------- project retirement


def cmd_memory_scan(args) -> int:
    """Find Claude Code memory files mentioning a project, without deleting anything.

    `retire-project.md` §1 is explicit that memory is not reliably scoped to one directory, so this
    searches every scope rather than just the project's own. Reporting only — deletion is a
    separate, confirmed step, per the same destructive-action discipline used everywhere here.
    """
    base = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(base):
        print("  no ~/.claude/projects directory")
        return 0
    needle = args.name.lower()
    hits = []
    for dirpath, _dirnames, filenames in os.walk(base):
        if os.path.basename(dirpath) != "memory":
            continue
        for name in filenames:
            if not name.endswith(".md"):
                continue
            full = os.path.join(dirpath, name)
            if needle in name.lower() or needle in read(full).lower():
                hits.append(full)
    if not hits:
        print(f"  no memory files mention {args.name!r}")
        return 0
    print(f"  {len(hits)} memory file(s) mention {args.name!r}:")
    for h in hits:
        print(f"    {h}")
    print()
    print(f"  {YELLOW}Nothing deleted.{RESET} Review each against close-down-session.md §2 first:")
    print("    - a general preference mislabelled as project-specific gets PROMOTED into groundwork")
    print("    - own-tooling findings and pure project status get dropped")
    return 0


# ---------------------------------------------------------------------------- layer direction

SPLIT_FILE = ".groundwork/split-base.txt"

#: A backticked path with an angle-bracket segment is a documented *pattern*, not a reference.
#: `cmd_paths`' own regex already excludes `<` from its character class, so these have never been
#: link-checked and no machinery is needed to keep skipping them. What is needed is the positive
#: rule below, so the convention stays true rather than staying true by accident.
PLACEHOLDER_OK = re.compile(r"<[a-z][a-z0-9-]*>")

DIRECTION_ALLOW = ".groundwork/direction-allow.txt"


def _direction_allow() -> set[tuple[str, str]]:
    """Cross-layer references that are correct as written, pinned to source AND literal.

    Pinning both is what stops the classic allowlist rot: an exemption written for one file would
    otherwise silently cover a real leak in another. A stale entry — one that no longer matches
    anything — is reported as a failure, so the file is forced to stay honest rather than
    accumulating dead lines nobody dares remove.
    """
    path = os.path.join(ROOT, DIRECTION_ALLOW)
    if not os.path.isfile(path):
        return set()
    out = set()
    for line in read(path).split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("::")]
        if len(parts) != 3 or not all(parts):
            continue
        out.add((parts[0], parts[1]))
    return out


def split_base() -> list[str] | None:
    """Which paths are destined for the base, or None meaning "this whole layer is the base".

    None is the case that matters for correctness: in the base repo itself there is no subset to
    carve out, and returning an empty list there would make `publishable` scan nothing and report
    green — a false pass in exactly the check whose job is to gate publication.
    """
    path = os.path.join(ROOT, SPLIT_FILE)
    if not os.path.isfile(path):
        return None
    return [
        line.strip()
        for line in read(path).split("\n")
        if line.strip() and not line.startswith("#")
    ]


def in_base(relative: str, rules: list[str] | None) -> bool:
    if rules is None:
        return True
    return any(relative.startswith(r) if r.endswith("/") else relative == r for r in rules)


def base_files(rules: list[str]) -> list[str]:
    """Every file destined for the base, whatever its extension — leaks are not markdown-only."""
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "graphify-out", "__pycache__", ".obsidian", ".groundwork"}]
        for name in filenames:
            full = os.path.join(dirpath, name)
            if in_base(rel(full), rules):
                out.append(full)

    return sorted(out)


#: Repo-relative paths named in backticks. Deliberately NOT run through `strip_code`: see
#: `cmd_direction`.
DIRECTION_PATH = re.compile(r"`((?:vault|standards|workflows|claude)/[\w./<>-]*)`")


def _layer_of(path: str, stack: list[dict]) -> dict | None:
    real = os.path.realpath(path)
    best = None
    for layer in stack:
        root = layer["root"]
        if real == root or real.startswith(root + os.sep):
            if best is None or len(layer["root"]) > len(best["root"]):
                best = layer
    return best


def cmd_direction(args) -> int:
    """A note in a lower layer may never reference a higher one.

    This is the invariant that makes the base publishable, and it is a property of the *stack*, not
    of a file list: for every reference, find the lowest-ranked layer it resolves in, and fail if
    that rank is above the referring note's own. A base note may name a private-layer *directory*
    (`standards/legal/`) — that exists in every layer — but never a private-layer *file*, which is
    one person's answer.

    **Scans raw text, not `strip_code` output**, and that is safer as well as more complete. The
    check only fires on a reference that actually resolves higher up, so the TOML array-of-table
    headers `strip_code` exists for can never be violations — they resolve nowhere. Keeping
    `strip_code` would instead hide the real ones: this repo writes wikilinks inside backticks.
    """
    stack = resolve_stack(ROOT)
    if len(stack) < 2:
        print(f"  {DIM}single-layer stack — nothing can be referenced upward{RESET}")
        return 0

    rank = {L["root"]: L["rank"] for L in stack}
    index = _link_index()
    allow, allow_used = _direction_allow(), set()
    problems = []

    tops = {"claude"}
    for layer in stack:
        tops.update(layer_config(layer["root"]).get("note_dirs", NOTE_DIRS))
    path_re = re.compile(r"`((?:" + "|".join(sorted(tops)) + r")/[\w./<>-]*)`")

    for path in stack_notes():
        src_layer = _layer_of(path, stack)
        if src_layer is None:
            continue
        src_rank = src_layer["rank"]
        source = f"{src_layer['name']}:{os.path.relpath(path, src_layer['root'])}"
        raw = read(path)

        for target in set(path_re.findall(raw)):
            if "<" in target:
                if not all(PLACEHOLDER_OK.fullmatch(seg)
                           for seg in re.findall(r"<[^>]*>", target)):
                    problems.append(f"{source}: `{target}` has a non-conforming placeholder")
                continue
            if target.endswith("/"):
                continue                      # a directory exists in every layer — allowed
            hits = [L for L in stack if os.path.exists(os.path.join(L["root"], target))]
            if hits and min(L["rank"] for L in hits) > src_rank:
                if (source, target) in allow:
                    allow_used.add((source, target))
                    continue
                problems.append(f"{source}: `{target}` only exists in a higher layer")

        for target in WIKILINK.findall(raw):
            target = " ".join(target.split())
            if not target:
                continue
            resolved = index.get(target.lower()) or index.get(target.rsplit("/", 1)[-1].lower())
            if not resolved:
                continue
            dst = _layer_of(resolved, stack)
            if dst and dst["rank"] > src_rank:
                if (source, target) in allow:
                    allow_used.add((source, target))
                    continue
                problems.append(f"{source}: [[{target}]] lives in a higher layer ({dst['name']})")

    for entry in sorted(set(allow) - allow_used):
        problems.append(f"stale allow entry matches nothing: {entry[0]} :: {entry[1]}")
    if allow_used:
        print(f"  {DIM}{len(allow_used)} allowed cross-layer reference(s){RESET}")
    print(f"  {DIM}{len(stack)} layers, {len(stack_notes())} notes checked{RESET}")
    return report("layer direction", problems)


# ------------------------------------------------------------------------------- publishability

#: IPv4 ranges that are documentation or private by definition, so they are exempt structurally
#: rather than as strings: a string allowlist of a /24 prefix also passes addresses one octet
#: longer, which is a silent hole exactly where the check is meant to be strict.
IP_EXEMPT = (
    ((192, 0, 2), 24), ((198, 51, 100), 24), ((203, 0, 113), 24),
    ((10,), 8), ((172, 16), 12), ((192, 168), 16), ((127,), 8),
)
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
GERMAN_ID = re.compile(r"\bHR[AB]\s?\d+\b|\bDE\d{9}\b|\bUSt-?IdNr\b")

#: Files that are per-layer state and must never reach the base at all.
LAYER_ARTIFACTS = ("link-baseline.txt", "commit-baseline.txt", "groundwork.toml", "split-base.txt")


def _ip_exempt(ip: str) -> bool:
    try:
        octets = [int(x) for x in ip.split(".")]
    except ValueError:
        return True
    if len(octets) != 4 or any(o > 255 for o in octets):
        return True                                    # not a real address
    if octets in ([0, 0, 0, 0], [255, 255, 255, 255]):
        return True
    for prefix, _bits in IP_EXEMPT:
        if octets[: len(prefix)] == list(prefix):
            return True
    return False


def cmd_publishable(args) -> int:
    """Would the base subset be safe to publish? Proven, not asserted.

    The `sensitivity: "real-identity"` frontmatter convention this repo advertises does not work:
    the grep its README recommends returns 7 files, 6 of which merely describe the convention, while
    the one note carrying five public IPs and four order numbers has no flag at all. A convention
    honoured once in four is not a guardrail.

    Known limitation, stated rather than implied away: this cannot catch prose leaks. "the failure on
    the payments repo's staging box" contains no matchable token and is still identifying.
    """
    rules = split_base()
    cfg = CONFIG.get("publishable", {})
    domains = cfg.get("domains", [])
    emails = cfg.get("emails", [])
    stems = cfg.get("repo_stems", [])

    domain_re = re.compile(
        r"(?i)(?<![A-Za-z0-9.-])(?:[A-Za-z0-9-]+\.)*(?:"
        + "|".join(re.escape(d) for d in domains) + r")\b") if domains else None
    email_re = re.compile("|".join(re.escape(e) for e in emails)) if emails else None
    stem_re = re.compile(r"\b(?:" + "|".join(re.escape(x) for x in stems)
                         + r")[a-z0-9_-]*\b") if stems else None

    problems = []
    for path in base_files(rules):
        source = rel(path)
        if os.path.basename(path) in LAYER_ARTIFACTS:
            problems.append(f"{source}: layer artifact must not reach the base")
            continue
        try:
            raw = read(path)
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for n, line in enumerate(raw.split("\n"), 1):
            for ip in IPV4.findall(line):
                if not _ip_exempt(ip):
                    problems.append(f"{source}:{n}: ipv4 {ip}")
            if email_re and email_re.search(line):
                problems.append(f"{source}:{n}: owned email")
            elif domain_re and domain_re.search(line):
                problems.append(f"{source}:{n}: owned domain")
            elif stem_re and stem_re.search(line):
                problems.append(f"{source}:{n}: owned repo/org name")
            if GERMAN_ID.search(line):
                problems.append(f"{source}:{n}: german registration identifier")

    files = len({p.split(":")[0] for p in problems})
    print(f"  {DIM}{len(problems)} line(s) across {files} file(s){RESET}")
    return report("publishable (base subset)", problems)


# ------------------------------------------------------------------------------- @-import paths

#: `@path` on its own line is how a command file or entry file pulls in another document. These are
#: invisible to `cmd_paths`, whose regex only matches backticked repo-relative paths — which is why
#: the layer split left five of six slash commands importing a file that no longer existed, with
#: every check green.
AT_IMPORT = re.compile(r"^@(\S+)\s*$", re.MULTILINE)

#: A `@`-import naming someone's home directory cannot work for anyone else, so it must never reach
#: a layer that ships to other people.
HOME_PATH = re.compile(r"^/(Users|home)/")


def _import_files(root: str = None) -> list[str]:
    root = root or ROOT
    out = []
    for sub in ("commands", "agents"):
        d = os.path.join(root, "claude", sub)
        for dirpath, _dirnames, filenames in os.walk(d):
            out.extend(os.path.join(dirpath, f) for f in filenames if f.endswith(".md"))
    entry = os.path.join(root, layer_config(root).get("entry_file", "claude/CLAUDE.md"))
    if os.path.isfile(entry):
        out.append(entry)
    return sorted(out)


#: `@~/.claude/groundwork/<handle>/<path inside that layer>`: how a command or entry file addresses a
#: note in a layer. The handle is `<rank>-<name>` from the stack manifest.
HANDLE_IMPORT = re.compile(r"^~/\.claude/groundwork/([^/]+)/(.+)$")


def _import_target(target: str, importer: str, stack: list[dict]) -> tuple[str | None, str | None]:
    """Where an `@`-import points, as (path, problem). Exactly one of the two is None.

    A layer handle is resolved against the *declared stack*, not against whatever happens to be in
    `~/.claude` right now. The handles only exist on disk after `link` has run, so checking the live
    directory made every check in a freshly cloned layer fail until the layer was assembled — and
    made the check depend on one machine's state. The stack is what `link` will write, so it is the
    thing to check.
    """
    handle = HANDLE_IMPORT.match(target)
    if handle:
        name, inside = handle.groups()
        for layer in stack:
            if layer_handle(layer) == name:
                return os.path.join(layer["root"], inside), None
        have = ", ".join(layer_handle(L) for L in stack) or "none"
        hint = (f" — the base layer must be declared as name = \"{BASE_NAME}\", rank = {BASE_RANK} "
                f"in groundwork.toml (`just new-layer` writes it that way)" if name == BASE_HANDLE else "")
        return None, f"@{target} names layer handle {name!r}, which is not in this stack ({have}){hint}"
    if target.startswith("~"):
        return os.path.expanduser(target), None
    if os.path.isabs(target):
        return target, None
    return os.path.normpath(os.path.join(os.path.dirname(importer), target)), None


def import_problems(roots: list[str], stack: list[dict]) -> list[str]:
    problems = []
    for root in roots:
        for path in _import_files(root):
            shown = os.path.relpath(path, root)
            for target in AT_IMPORT.findall(read(path)):
                if HOME_PATH.match(target):
                    problems.append(f"{shown}: @{target} hardcodes a home directory — "
                                    f"use ~/.claude/groundwork/<NN>-<layer>/… instead")
                    continue
                resolved, problem = _import_target(target, path, stack)
                if problem:
                    problems.append(f"{shown}: {problem}")
                elif not os.path.isfile(resolved):
                    problems.append(f"{shown}: @{target} resolves to nothing")
    return problems


def cmd_imports(_args) -> int:
    """Every `@path` import must resolve, and must not name a home directory."""
    return report(f"@-imports ({len(_import_files())} files)",
                  import_problems([ROOT], resolve_stack(ROOT)))


# --------------------------------------------------------------------------- assembling ~/.claude

CLAUDE_DIR = os.path.expanduser("~/.claude")
GROUNDWORK_DIR = os.path.join(CLAUDE_DIR, "groundwork")

#: Merged per file. A skill is merged per top-level directory instead: it is a directory with a
#: `SKILL.md` and usually `references/`, and splitting one across layers is incoherent.
MERGE_FILES = ("commands", "agents")
MERGE_DIRS = ("skills",)
SETTINGS_FILE = "claude/settings.json"


def _declared_target(path: str) -> str:
    """Where a symlink points, resolved ONE level only."""
    target = os.readlink(path)
    if not os.path.isabs(target):
        target = os.path.join(os.path.dirname(path), target)
    return os.path.normpath(target)


def _owned(path: str, roots: list[str]) -> bool:
    """Is this a symlink we created — one pointing into a layer we know about?

    Compares the *declared* target, not `realpath`. A layer may legitimately hold a symlink that
    leaves the repo — a skill directory that is a symlink to a sibling clone — and resolving
    transitively would classify our own link as a stranger, so it would never be cleaned up and the
    next run would die on FileExistsError instead of being idempotent.
    """
    if not os.path.islink(path):
        return False
    target = _declared_target(path)
    return any(target == r or target.startswith(r + os.sep) for r in roots)


def _clear(directory: str, roots: list[str], strangers: list[str],
           ignore: set[str] | None = None) -> None:
    """Remove only our own links. Anything else is reported, never deleted.

    `close-down-session.md` records the incident this guards against: a literal reading of a
    hardcoded list would have deleted `commands/`, breaking every slash command including that
    workflow's own. So this removes what it can prove it owns and leaves the rest alone.
    """
    if not os.path.isdir(directory):
        return
    for name in sorted(os.listdir(directory)):
        if ignore and name in ignore:
            continue                       # our own generated files, rewritten below
        full = os.path.join(directory, name)
        if _owned(full, roots):
            os.unlink(full)
        else:
            strangers.append(os.path.relpath(full, CLAUDE_DIR))


LEGACY_ASSEMBLY_DIR = os.path.join(CLAUDE_DIR, LEGACY_ASSEMBLY)


def _legacy_roots() -> list[str]:
    """Where the handles of a pre-groundwork `~/.claude/hafen/` point: layers this machine had."""
    if os.path.islink(LEGACY_ASSEMBLY_DIR) or not os.path.isdir(LEGACY_ASSEMBLY_DIR):
        return []
    return sorted({_declared_target(os.path.join(LEGACY_ASSEMBLY_DIR, name))
                   for name in os.listdir(LEGACY_ASSEMBLY_DIR)
                   if os.path.islink(os.path.join(LEGACY_ASSEMBLY_DIR, name))})


def _remove_legacy_assembly(legacy_roots: list[str], warnings: list[str]) -> int:
    """Remove the old `~/.claude/hafen/` once the new assembly is in place. Returns entries removed.

    Only what the old `link` wrote goes: handle symlinks, `ROOTS` and `INDEX.md`. The directory is
    removed only when that leaves it empty, so anything else in it is reported and kept.
    """
    if os.path.islink(LEGACY_ASSEMBLY_DIR) or not os.path.isdir(LEGACY_ASSEMBLY_DIR):
        return 0
    removed = 0
    for name in sorted(os.listdir(LEGACY_ASSEMBLY_DIR)):
        full = os.path.join(LEGACY_ASSEMBLY_DIR, name)
        ours = (os.path.islink(full) and _owned(full, legacy_roots)) or \
            (name in ("ROOTS", "INDEX.md") and os.path.isfile(full) and not os.path.islink(full))
        if ours:
            os.unlink(full)
            removed += 1
    try:
        os.rmdir(LEGACY_ASSEMBLY_DIR)
    except OSError:
        warnings.append(f"left alone (not ours): {LEGACY_ASSEMBLY_DIR} still holds "
                        f"{', '.join(sorted(os.listdir(LEGACY_ASSEMBLY_DIR)))}")
    return removed


def cmd_link(args) -> int:
    """Assemble ~/.claude from the layer stack. Idempotent; safe to re-run."""
    stack = resolve_stack(ROOT)
    roots = [L["root"] for L in stack]
    problems, warnings, strangers = [], [], []
    # A machine switched over from the old mechanism still has `~/.claude/hafen/` and links into the
    # old base. Those links are ours too: without this they would be left as strangers and fail
    # `symlinks` for pointing outside every declared layer.
    legacy_roots = _legacy_roots()
    owned_roots = roots + legacy_roots

    if not CONFIG.get("assembled", True):
        problems.append("this layer is not the assembled top (assembled = false in groundwork-layer.toml). "
                        "To stack your own layer on top of it, run `just new-layer <path>` here, "
                        "then `just link` from <path>.")
        return report("assemble ~/.claude", problems)

    os.makedirs(GROUNDWORK_DIR, exist_ok=True)

    # 1. Stable path handles. Absolute, because ~/.claude never moves with your repos — a
    #    relative link only survives a move when BOTH ends move together, which these never do.
    _clear(GROUNDWORK_DIR, owned_roots, strangers, ignore={"ROOTS", "INDEX.md"})
    for layer in stack:
        link = os.path.join(GROUNDWORK_DIR, layer_handle(layer))
        if os.path.islink(link) or os.path.exists(link):
            os.unlink(link)
        os.symlink(layer["root"], link)

    # 2. ROOTS — the grep enabler. `grep -r` and ripgrep both refuse to descend into a symlinked
    #    directory found during recursion, so the handles above are invisible to them. Command-line
    #    arguments ARE followed: `rg 'x' $(cat ~/.claude/groundwork/ROOTS)`.
    with open(os.path.join(GROUNDWORK_DIR, "ROOTS"), "w", encoding="utf-8") as f:
        f.write("".join(r + "\n" for r in roots))

    # 3. INDEX.md — a real file, so `grep -r` over ~/.claude sees every note in every layer.
    lines = ["# Every note in the stack", "",
             "Generated by `just link`. Not committed to any layer: it would embed one layer's",
             "note titles in another's repo.", ""]
    for layer in stack:
        dirs = tuple(layer_config(layer["root"]).get("note_dirs", NOTE_DIRS))
        for d in dirs:
            for dirpath, dirnames, filenames in os.walk(os.path.join(layer["root"], d)):
                dirnames[:] = [x for x in dirnames
                               if x not in {".git", "graphify-out", "__pycache__"}]
                for name in sorted(filenames):
                    if not name.endswith(".md") or name == MAP_NAME:
                        continue
                    full = os.path.join(dirpath, name)
                    relative = os.path.relpath(full, layer["root"])
                    lines.append(f"- `{layer['name']}` — {map_title(full)} — `{relative}`")
    with open(os.path.join(GROUNDWORK_DIR, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    # 4. The entry file: highest-ranked layer that provides one wins, so a base-only stack still
    #    gets a router. A symlink, never a generated concatenation — "editing either path edits the
    #    same file, no sync step" is the property that makes this repo worth having, and a generated
    #    file would be silently clobbered by the next run of this command.
    entry_src = None
    for layer in stack:
        candidate = os.path.join(layer["root"], layer_config(layer["root"]).get("entry_file", "claude/CLAUDE.md"))
        if os.path.isfile(candidate):
            entry_src = candidate
    entry_link = os.path.join(CLAUDE_DIR, "CLAUDE.md")
    if entry_src:
        if os.path.islink(entry_link):
            os.unlink(entry_link)
        elif os.path.exists(entry_link):
            problems.append("~/.claude/CLAUDE.md is a real file, not a symlink — refusing to replace it")
        if not os.path.exists(entry_link):
            os.symlink(entry_src, entry_link)

    # 4b. Settings: same rule as the entry file — highest layer providing `claude/settings.json`
    #     wins, linked, never copied, so a new machine gets the same model, permissions and auto
    #     mode from `just link` alone. settings.local.json stays per machine and is never linked.
    settings_src = None
    for layer in stack:
        candidate = os.path.join(layer["root"], SETTINGS_FILE)
        if os.path.isfile(candidate):
            settings_src = candidate
    settings_link = os.path.join(CLAUDE_DIR, "settings.json")
    if settings_src:
        if os.path.islink(settings_link):
            os.unlink(settings_link)
        elif os.path.exists(settings_link):
            problems.append("~/.claude/settings.json is a real file, not a symlink — refusing to "
                            "replace it; move what it holds into a layer's claude/settings.json first")
        if not os.path.exists(settings_link):
            os.symlink(settings_src, settings_link)

    # 5. Merge commands/, agents/ per file and skills/ per top-level directory. Later layer wins.
    for kind, per_dir in [(k, False) for k in MERGE_FILES] + [(k, True) for k in MERGE_DIRS]:
        dest = os.path.join(CLAUDE_DIR, kind)
        if os.path.islink(dest):
            os.unlink(dest)
        os.makedirs(dest, exist_ok=True)
        _clear(dest, owned_roots, strangers)

        winners: dict[str, tuple[str, str]] = {}
        folded: dict[str, str] = {}
        for layer in stack:
            src = os.path.join(layer["root"], "claude", kind)
            if not os.path.isdir(src):
                continue
            for name in sorted(os.listdir(src)):
                full = os.path.join(src, name)
                if per_dir and not (os.path.isdir(full) or os.path.islink(full)):
                    continue
                if not per_dir and not name.endswith(".md"):
                    continue
                # APFS is case-insensitive: two layers differing only in case would collide into
                # one entry non-deterministically. Fail rather than pick one.
                key = name.casefold()
                if key in folded and folded[key] != name:
                    problems.append(f"{kind}/: case-folded collision between "
                                    f"{folded[key]!r} and {name!r}")
                folded[key] = name
                if name in winners:
                    warnings.append(f"{kind}/{name}: {layer['name']} shadows "
                                    f"{winners[name][0]}")
                winners[name] = (layer["name"], full)

        for name, (_layer, full) in sorted(winners.items()):
            link = os.path.join(dest, name)
            if os.path.islink(link):
                os.unlink(link)
            elif os.path.exists(link):
                problems.append(f"{kind}/{name}: a real file is in the way — left untouched")
                continue
            os.symlink(full, link)

    for stranger in sorted(set(strangers)):
        warnings.append(f"left alone (not ours): ~/.claude/{stranger}")

    if legacy_roots or os.path.isdir(LEGACY_ASSEMBLY_DIR):
        gone = _remove_legacy_assembly(legacy_roots, warnings)
        print(f"  {DIM}removed the legacy ~/.claude/{LEGACY_ASSEMBLY}/ assembly ({gone} entr(y/ies)){RESET}")

    # 6. Every `@`-import shipped by any layer must now resolve. A stack that names its base layer
    #    anything but `base` at rank 0 links cleanly and then loads every command as an empty file,
    #    which nothing would notice until a command was run.
    problems.extend(import_problems(roots, stack))

    names = ", ".join(L["name"] for L in stack)
    print(f"  {DIM}{len(stack)} layer(s), lowest rank first: {names}{RESET}")
    return report("assemble ~/.claude", problems, warnings)


# ----------------------------------------------------------------------------------- new layer

LAYER_NAME = re.compile(r"[a-z][a-z0-9-]*")

LAYER_JUSTFILE = """# {name}: a groundwork layer stacked on the base.
#
# Every recipe lives in the base layer's `groundwork.just`, reached through `.groundwork/base`, a relative
# symlink to the base clone. `import?`, not `import`: a clone of this layer on a machine without the
# base then fails loudly on an unknown recipe, instead of a mandatory import making this whole file
# unparseable.

import? '.groundwork/base/groundwork.just'
"""

LAYER_TOML = """# What this layer is, for the shared mechanism in the base layer's `bin/gwk.py`.
#
# `note_dirs` is DECLARED, not detected: a missing directory is then a hard failure instead of a
# silent pass.

schema = 1
name = "{name}"
note_dirs = ["vault", "standards", "workflows"]
entry_file = "claude/CLAUDE.md"
entry_max_words = 400

# This layer owns ~/.claude's symlinks (`just link`). Exactly one layer in a stack sets this.
assembled = true

# A layer that commits straight to one branch, with no issue tracker, needs no trailing (#N) in
# commit subjects. Use "issue" if this repo tracks its work in issues.
commit_reference = "none"

[map.vault]
heading = "Knowledge base"
purpose = "Durable facts and findings. Check here before a web search."

[map.standards]
heading = "Standing preferences and defaults"
purpose = "What to reach for when nothing about the task says otherwise: your vendors, stack and jurisdiction."

[map.workflows]
heading = "Process specs"
purpose = "The concrete how for a recurring kind of work, as you do it."

# Identifiers this layer must never leak into a layer beneath it. Filled in by whoever publishes a
# lower layer; `just publish-check` is only as strict as these lists.
[publishable]
domains    = []
emails     = []
repo_stems = []
"""

LAYER_MANIFEST = """# The layer stack, lowest rank first. Owned by the TOP layer only: a lower layer naming a higher one
# is exactly the direction violation `just publish-check` exists to forbid.
#
# Paths are relative to this file's directory. The base layer must be named "{base_name}" at rank
# {base_rank}: the shipped slash commands import it as ~/.claude/groundwork/{base_handle}/. Ranks are
# gapped by 10 so a layer can be inserted without renumbering.

schema = 1

[[layer]]
name = "{base_name}"
path = ".groundwork/base"
rank = {base_rank}

[[layer]]
name = "{name}"
path = "."
rank = {rank}
"""

LAYER_ENTRY = """# CLAUDE.md: {name}

@~/.claude/groundwork/{base_handle}/claude/CLAUDE.md

Your own routing rows, vendors, jurisdiction and standing preferences go here or in the notes this
file points at. The base layer's entry file above holds the workflow; this one adds only what is
yours. Keep it a router: it is loaded into every session, and `just entry` enforces a word budget.
"""


def cmd_new_layer(args) -> int:
    """Create an empty private layer, stacked on this base, that passes every check as it stands.

    Everything the README used to ask a newcomer to hand-write (the manifest, the layer file, the
    `.groundwork/base` symlink, the justfile, the entry file) is written here, so the one thing a
    stranger can get wrong is not typing it out. Refuses a non-empty target rather than merging
    into it.
    """
    target = os.path.abspath(os.path.expanduser(args.path))
    name = args.name or re.sub(r"[^a-z0-9-]+", "-", os.path.basename(target).lower()).strip("-")
    if not LAYER_NAME.fullmatch(name or ""):
        print(f"  {RED}FAIL{RESET}  layer name {name!r} must be lowercase letters, digits and "
              f"hyphens, starting with a letter — pass --name")
        return 1
    if name == BASE_NAME:
        print(f"  {RED}FAIL{RESET}  {BASE_NAME!r} is the name of the base layer — choose another")
        return 1
    author_name = (args.author_name or os.environ.get("GWK_AUTHOR_NAME", "")).strip()
    author_email = (args.author_email or os.environ.get("GWK_AUTHOR_EMAIL", "")).strip()
    if bool(author_name) != bool(author_email):
        print(f"  {RED}FAIL{RESET}  an identity needs both a name and an email — give both "
              f"(--author-name/--author-email or GWK_AUTHOR_NAME/GWK_AUTHOR_EMAIL) or neither")
        return 1
    if os.path.exists(target) and os.listdir(target):
        print(f"  {RED}FAIL{RESET}  {target} exists and is not empty — refusing to write into it")
        return 1
    if os.path.realpath(target) == os.path.realpath(BASE_ROOT) or \
            os.path.realpath(target).startswith(os.path.realpath(BASE_ROOT) + os.sep):
        print(f"  {RED}FAIL{RESET}  a layer cannot live inside the base clone — choose another path")
        return 1

    for d in ("vault", "standards", "workflows", "claude/commands", ".groundwork"):
        os.makedirs(os.path.join(target, d), exist_ok=True)

    def write(relative: str, text: str) -> None:
        with open(os.path.join(target, relative), "w", encoding="utf-8", newline="") as f:
            f.write(text)

    fields = dict(name=name, rank=BASE_RANK + 10, base_name=BASE_NAME, base_rank=BASE_RANK,
                  base_handle=BASE_HANDLE)
    write("groundwork-layer.toml", LAYER_TOML.format(**fields))
    write("groundwork.toml", LAYER_MANIFEST.format(**fields))
    write("justfile", LAYER_JUSTFILE.format(**fields))
    write("claude/CLAUDE.md", LAYER_ENTRY.format(**fields))
    # Identity is the one thing the base cannot make up: a placeholder would let `just commit` run
    # under a name nobody chose, and reading git config is what the commit rule forbids. So the
    # files exist only when the author is given, and are ignored either way, since an email
    # address does not belong in a layer that may one day be published.
    if author_name:
        write(".groundwork/author-name", author_name + "\n")
        write(".groundwork/author-email", author_email + "\n")
    write(".gitignore", ".DS_Store\n__pycache__/\n*.py[cod]\n.groundwork/author-*\n")
    write("SESSION_LOG.md", "# Session Log\n")
    for d in ("vault", "standards", "workflows"):
        write(f"{d}/README.md", f"---\ntitle: \"{d} of the {name} layer\"\ntype: \"index\"\n"
                                f"category: \"{d}\"\n---\n\nNotes go here, one topic per file, "
                                f"each with `title` and `type` frontmatter.\n")
    # Relative, so the whole tree of repos moves as one. Computed from the real path of `.groundwork`:
    # a link is resolved against the directory it actually lives in, so a target reached through a
    # symlinked parent (macOS's /var -> /private/var) would otherwise get one `..` too few.
    groundwork_real = os.path.realpath(os.path.join(target, ".groundwork"))
    os.symlink(os.path.relpath(os.path.realpath(BASE_ROOT), groundwork_real),
               os.path.join(target, ".groundwork", "base"))

    # A repository, so the commit-msg hook and the history check have something to work on. No
    # commit is made: the layer is yours to commit, under your own identity.
    if subprocess.run(["git", "init", "-q", "-b", "main", target]).returncode != 0:
        print(f"  {RED}FAIL{RESET}  git init failed in {target}")
        return 1

    print(f"  {GREEN}created{RESET} layer {name!r} at {target}")
    print(f"  {DIM}stack: {BASE_HANDLE} -> {BASE_ROOT}{RESET}")
    if author_name:
        print(f"  {DIM}identity for `just commit` written to .groundwork/author-name and "
              f".groundwork/author-email (git-ignored){RESET}")
    else:
        print("  `just commit` needs an identity: set GWK_AUTHOR_NAME and GWK_AUTHOR_EMAIL, or write "
              ".groundwork/author-name and .groundwork/author-email")
    print("  next, from that directory:  just install-hooks && just map && just link && just doctor")
    return 0


# ------------------------------------------------------------- migrate-from-heimathafen

#: The generated-file header every `MAP.md` of the old mechanism carried. It names a command that no
#: longer exists, so the whole block is swapped for the current one, byte for byte, instead of being
#: left to make `map --check` fail in every directory.
LEGACY_MAP_PREAMBLE = """<!-- GENERATED by `hafen map` from each note's frontmatter — never hand-edit.
     `hafen doctor` fails when this file no longer matches the tree.
     To change an entry, change that note's `title:`. To add one, add the note. -->"""

#: A reference followed by `:<digits>` cites a line of that file as it was ("`hafen.just:292`"). The
#: line number belongs to the old file, so the citation is history and stays as written.
_NOT_A_CITATION = r"(?!:\d)"
_ENV_SUFFIXES = "AUTHOR_NAME|AUTHOR_EMAIL|COMMIT_REFERENCE|PROJECTS_DIR|BRANCH"

#: (kind, pattern, replacement). Every pattern names one mechanism path or variable exactly, with a
#: boundary on both sides, so `hafen.de`, "Hafenwasser", `linkhafen` and prose about "heimathafen"
#: never match. A new rule needs the same property.
MIGRATION_RULES = (
    ("assembly-path", re.compile(r"\.claude/hafen(?![\w-])"), ".claude/groundwork"),
    # The same directory named relative to ~/.claude: `hafen/ROOTS`, `hafen/INDEX.md`, `hafen/<handle>`.
    ("assembly-path", re.compile(r"(?<![\w./~-])hafen/(?=ROOTS\b|INDEX\.md|<|\d\d-)"), "groundwork/"),
    ("layer-file", re.compile(r"(?<![\w.-])hafen-layer\.toml" + _NOT_A_CITATION), LAYER_FILE),
    ("stack-file", re.compile(r"(?<![\w.-])hafen\.toml" + _NOT_A_CITATION), STACK_FILE),
    ("recipes-file", re.compile(r"(?<![\w.-])hafen\.just" + _NOT_A_CITATION), RECIPES_FILE),
    ("state-dir", re.compile(r"(?<![\w.~-])\.hafen(?![\w.-])"), STATE_DIR),
    ("script-path", re.compile(r"(?<![\w.-])(bin/)?hh\.py(?![\w-])" + _NOT_A_CITATION), r"\1gwk.py"),
    # The commands of the `hafen` program that preceded hh.py; each is a recipe of the same name now.
    ("cli-command", re.compile(r"(?<![\w./-])hafen (map|doctor|publish-check|link|entry)(?![\w-])"),
     r"just \1"),
    ("env-var", re.compile(r"\bHH_(" + _ENV_SUFFIXES + r")\b"), r"GWK_\1"),
    ("env-var", re.compile(r"\bHAFEN_LAYER\b"), "GWK_LAYER"),
    ("test-recipe", re.compile(r"(?<![\w.-])hh-test\b"), "gwk-test"),
    ("moved-base-file", re.compile(r"(?<![\w-])workflows/heimathafen/"), "workflows/groundwork/"),
    ("moved-base-file", re.compile(r"(?<![\w-])heimathafen-self-review(?![\w-])"),
     "groundwork-self-review"),
)

#: Directories whose contents are not the layer's own text: history, caches, editor and graph state.
MIGRATION_SKIP_DIRS = {".git", "graphify-out", ".obsidian", "node_modules", "__pycache__"}
MIGRATION_MAX_BYTES = 4 * 1024 * 1024


def _read_text_or_none(path: str) -> str | None:
    """The file's text, byte for byte (no newline translation), or None when it is not text."""
    try:
        if os.path.getsize(path) > MIGRATION_MAX_BYTES:
            return None
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    if b"\0" in raw:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


COMMIT_REFERENCE_KEY = re.compile(r"(?m)^commit_reference\s*=")

#: The old mechanism had no `commit_reference` key: it required a scope and never an issue
#: reference. The new default is `"issue"`, so a migrated layer says `"none"` out loud, or its whole
#: history would fail `check-log` the day the base is switched.
COMMIT_REFERENCE_ADDED = (
    "# Added by migrate-from-heimathafen: the old mechanism required a scope and never an issue\n"
    "# reference, which is what \"none\" means. Use \"issue\" if this layer tracks its work in issues.\n"
    "commit_reference = \"none\"\n")


def add_commit_reference(text: str) -> tuple[str, int]:
    """Add `commit_reference = "none"` to a layer file that has no such key. Returns (text, added).

    TOML wants top-level keys before the first table, so the key goes just above the first `[table]`
    header, and above the comment lines that belong to that header.
    """
    if COMMIT_REFERENCE_KEY.search(text):
        return text, 0
    lines = text.split("\n")
    header = next((i for i, line in enumerate(lines) if line.startswith("[")), None)
    if header is None:
        return text.rstrip("\n") + "\n\n" + COMMIT_REFERENCE_ADDED, 1
    at = header
    while at > 0 and lines[at - 1].startswith("#"):
        at -= 1
    block = COMMIT_REFERENCE_ADDED.rstrip("\n").split("\n") + [""]
    return "\n".join(lines[:at] + block + lines[at:]), 1


def migrate_text(text: str, name: str) -> tuple[str, dict[str, int]]:
    """Apply every migration rule to one file's text. Returns the new text and counts per kind."""
    counts: dict[str, int] = {}
    if name == MAP_NAME and LEGACY_MAP_PREAMBLE in text:
        counts["map-preamble"] = text.count(LEGACY_MAP_PREAMBLE)
        text = text.replace(LEGACY_MAP_PREAMBLE, MAP_PREAMBLE)
    for kind, pattern, replacement in MIGRATION_RULES:
        text, n = pattern.subn(replacement, text)
        if n:
            counts[kind] = counts.get(kind, 0) + n
    return text, counts


def _after_rename(relative: str) -> str:
    """Where a path inside a layer will be once the three legacy names have been renamed."""
    renames = {LEGACY_LAYER_FILE: LAYER_FILE, LEGACY_STACK_FILE: STACK_FILE}
    if relative in renames:
        return renames[relative]
    head, sep, tail = relative.partition("/")
    if head == LEGACY_STATE_DIR:
        return STATE_DIR + sep + tail
    return relative


def _is_old_style_layer(path: str) -> bool:
    """Does a directory still use the legacy layer file and not yet the current one?"""
    return (os.path.isfile(os.path.join(path, LEGACY_LAYER_FILE))
            and not os.path.isfile(os.path.join(path, LAYER_FILE)))


def _is_old_base(path: str) -> bool:
    """An old-style layer that ships the mechanism itself, i.e. the base, not a private layer."""
    return _is_old_style_layer(path) and (
        os.path.isfile(os.path.join(path, LEGACY_RECIPES_FILE))
        or os.path.isfile(os.path.join(path, "bin", "hh.py")))


def _is_new_base(path: str) -> bool:
    return (os.path.isfile(os.path.join(path, LAYER_FILE))
            and os.path.isfile(os.path.join(path, "bin", "gwk.py"))
            and os.path.isfile(os.path.join(path, RECIPES_FILE)))


def _relative_link(target: str, link_dir: str) -> str:
    """A relative symlink target from a directory, computed from real paths (see `new-layer`)."""
    return os.path.relpath(os.path.realpath(target), os.path.realpath(link_dir))


def is_excluded(relative: str, excludes: tuple[str, ...], defaults: bool = True) -> str | None:
    """Why a layer file keeps its old wording, or None when the migration may rewrite it.

    `excludes` are globs (`fnmatch`, so `*` also crosses `/`). A glob without a `/` is tested against
    the file's name at any depth; one with a `/` against the whole path relative to the layer. With
    `defaults`, a dated record (`is_dated_record`) is excluded as well.
    """
    for pattern in excludes:
        target = relative if "/" in pattern else os.path.basename(relative)
        if fnmatch.fnmatchcase(target, pattern):
            return f"--exclude {pattern}"
    if defaults and is_dated_record(relative):
        return "dated record"
    return None


def plan_migration(root: str, new_base: str | None, excludes: tuple[str, ...] = (),
                   defaults: bool = True) -> dict:
    """Everything the migration would do to one layer, computed without writing anything.

    The returned plan lists renames, the base symlink, the files to rewrite (with their new text and
    counts per kind), the files kept as written because of an exclude (only those that would have
    changed) and the files that were not text. `refusals` is non-empty when the layer cannot be
    migrated; nothing else in the plan is meaningful then.
    """
    plan: dict = {"root": root, "renames": [], "symlink": None, "rewrites": [], "kept": [],
                  "skipped": [], "notices": [], "refusals": []}
    refusals = plan["refusals"]
    for name in (LEGACY_LAYER_FILE, LEGACY_STACK_FILE):
        if is_excluded(name, excludes, defaults=False):
            refusals.append(f"an --exclude matches {name}: the migration must rewrite it "
                            f"(it carries the layer's settings), so it cannot be kept as it was")
    if refusals:
        return plan

    if _is_old_base(root):
        refusals.append("this is an old base (it ships hafen.just or bin/hh.py), not a private layer: "
                        "the old base is replaced by the new one, never migrated in place")
        return plan
    has_legacy = [n for n in (LEGACY_LAYER_FILE, LEGACY_STACK_FILE, LEGACY_STATE_DIR)
                  if os.path.lexists(os.path.join(root, n))]
    if not has_legacy:
        if os.path.isfile(os.path.join(root, LAYER_FILE)):
            plan["notices"].append("already migrated: no legacy names found, nothing to do")
        else:
            refusals.append(f"no {LEGACY_LAYER_FILE} and no {LAYER_FILE}: not a layer")
        return plan
    if not os.path.isfile(os.path.join(root, LEGACY_LAYER_FILE)):
        refusals.append(f"{LEGACY_LAYER_FILE} is missing: not a layer of the old mechanism")
        return plan
    for old, new in ((LEGACY_LAYER_FILE, LAYER_FILE), (LEGACY_STACK_FILE, STACK_FILE),
                     (LEGACY_STATE_DIR, STATE_DIR)):
        if os.path.lexists(os.path.join(root, old)) and os.path.lexists(os.path.join(root, new)):
            refusals.append(f"both {old} and {new} exist: a half-finished migration, resolve it by hand")
    if refusals:
        return plan

    for old, new, kind in ((LEGACY_LAYER_FILE, LAYER_FILE, "file"), (LEGACY_STACK_FILE, STACK_FILE, "file"),
                           (LEGACY_STATE_DIR, STATE_DIR, "directory")):
        if os.path.lexists(os.path.join(root, old)):
            plan["renames"].append((kind, old, new))

    # The base symlink. It moves with its directory. Its target is replaced only when it names an
    # old base, because a symlink to a middle layer is a legitimate stack and stays as it is.
    link = os.path.join(root, LEGACY_STATE_DIR, "base")
    if os.path.islink(link):
        current = os.readlink(link)
        resolved = os.path.realpath(link)
        replacement = None
        if new_base is not None:
            replacement = new_base
        elif _is_old_base(resolved):
            replacement = BASE_ROOT
        if replacement is not None:
            if not _is_new_base(replacement):
                refusals.append(f"{replacement} is not a groundwork base (it needs {LAYER_FILE}, "
                                f"{RECIPES_FILE} and bin/gwk.py)")
                return plan
            new_target = _relative_link(replacement, os.path.join(os.path.realpath(root), STATE_DIR))
            plan["symlink"] = (f"{STATE_DIR}/base", current, new_target)
        elif not os.path.exists(link):
            plan["notices"].append(f"{STATE_DIR}/base is a dangling symlink to {current}: pass --base "
                                   f"<new base clone> to repoint it")
        elif _is_old_style_layer(resolved):
            plan["notices"].append(f"{STATE_DIR}/base points at {resolved}, an old-style layer that is "
                                   f"not a base: migrate that layer too, it is part of this stack")
    elif os.path.lexists(link):
        plan["notices"].append(f"{LEGACY_STATE_DIR}/base is not a symlink: left as it is")

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in MIGRATION_SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            relative = os.path.relpath(full, root)
            text = _read_text_or_none(full)
            if text is None:
                plan["skipped"].append(relative)
                continue
            new_text, counts = migrate_text(text, name)
            why = is_excluded(relative, excludes, defaults)
            if why:
                if new_text != text:
                    plan["kept"].append({"old": relative, "why": why, "counts": counts})
                continue
            if relative == LEGACY_LAYER_FILE:
                new_text, added = add_commit_reference(new_text)
                if added:
                    counts["config-key"] = added
            if new_text != text:
                plan["rewrites"].append({"old": relative, "new": _after_rename(relative),
                                         "counts": counts, "text": new_text})
    return plan


def _git_state(root: str) -> tuple[str | None, list[str]]:
    """(problem, dirty lines): a problem when `root` is not the top of a git repository."""
    top = subprocess.run(["git", "-C", root, "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    if top.returncode != 0 or os.path.realpath(top.stdout.strip()) != os.path.realpath(root):
        return "not the top of a git repository", []
    status = subprocess.run(["git", "-C", root, "status", "--porcelain"],
                            capture_output=True, text=True)
    return None, [line for line in status.stdout.split("\n") if line.strip()]


def _print_migration(plan: dict, verb: str) -> None:
    for kind, old, new in plan["renames"]:
        print(f"  {verb} rename   {old}{'/' if kind == 'directory' else ''} -> "
              f"{new}{'/' if kind == 'directory' else ''}")
    if plan["symlink"]:
        path, old, new = plan["symlink"]
        print(f"  {verb} symlink  {path}: {old} -> {new}")
    for item in plan["rewrites"]:
        what = ", ".join(f"{k} x{n}" for k, n in sorted(item["counts"].items()))
        shown = item["old"] if item["old"] == item["new"] else f"{item['old']} (as {item['new']})"
        print(f"  {verb} rewrite  {shown}  [{what}]")
    for item in plan["kept"]:
        what = ", ".join(f"{k} x{n}" for k, n in sorted(item["counts"].items()))
        label = "would keep" if verb == "would" else "kept"
        print(f"  {label:<12}   {item['old']}  [{item['why']}; not rewritten: {what}]")


def migration_summary(plan: dict) -> list[str]:
    """Counts per kind of change, as printed lines."""
    files = sum(1 for k, _o, _n in plan["renames"] if k == "file")
    dirs = sum(1 for k, _o, _n in plan["renames"] if k == "directory")
    per_kind: dict[str, list[int]] = {}
    for item in plan["rewrites"]:
        for kind, n in item["counts"].items():
            entry = per_kind.setdefault(kind, [0, 0])
            entry[0] += 1
            entry[1] += n
    total = sum(v[1] for v in per_kind.values())
    lines = [f"renames:            {files + dirs}  ({files} file(s), {dirs} directory)",
             f"base symlink:       {1 if plan['symlink'] else 0} repointed",
             f"files rewritten:    {len(plan['rewrites'])}  ({total} replacement(s))"]
    for kind in sorted(per_kind):
        lines.append(f"  {kind + ':':<18}{per_kind[kind][0]} file(s), {per_kind[kind][1]} replacement(s)")
    kept = sum(sum(item["counts"].values()) for item in plan["kept"])
    lines.append(f"kept as written:    {len(plan['kept'])}  ({kept} replacement(s) not made, excluded)")
    lines.append(f"not text, skipped:  {len(plan['skipped'])}")
    return lines


def apply_migration(plan: dict) -> None:
    """Write the plan. Content first, at the old paths, then the renames, then the symlink."""
    root = plan["root"]
    for item in plan["rewrites"]:
        with open(os.path.join(root, item["old"]), "w", encoding="utf-8", newline="") as f:
            f.write(item["text"])
    for _kind, old, new in plan["renames"]:
        os.rename(os.path.join(root, old), os.path.join(root, new))
    if plan["symlink"]:
        path, _old, new_target = plan["symlink"]
        link = os.path.join(root, path)
        os.unlink(link)
        os.symlink(new_target, link)


def cmd_migrate(args) -> int:
    """Rewrite one private layer from the heimathafen names to the groundwork names.

    Mechanical only: three renames (the layer file, the stack file, the state directory), the base
    symlink, and a fixed table of exact references (`MIGRATION_RULES`). The layer's notes keep every
    other word. It makes no commit and does not touch `.git`; a clean working tree is the rollback.
    """
    root = os.path.abspath(os.path.expanduser(args.layer))
    if not os.path.isdir(root):
        print(f"  {RED}FAIL{RESET}  {root} is not a directory")
        return 1
    new_base = os.path.abspath(os.path.expanduser(args.base)) if args.base else None
    excludes = tuple(args.exclude or ())
    defaults = not args.no_default_excludes

    plan = plan_migration(root, new_base, excludes, defaults)
    if plan["refusals"]:
        for r in plan["refusals"]:
            print(f"  {RED}FAIL{RESET}  {r}")
        return 1

    git_problem, dirty = _git_state(root)
    if not args.dry_run:
        if git_problem:
            print(f"  {RED}FAIL{RESET}  {root} is {git_problem}: refusing to rewrite a layer "
                  f"that git cannot restore")
            return 1
        if dirty:
            print(f"  {RED}FAIL{RESET}  the working tree is not clean ({len(dirty)} path(s)): commit or "
                  f"set aside your own changes first, so that this migration is the only diff")
            for line in dirty[:10]:
                print(f"    {line}")
            return 1

    print(f"  {DIM}{'dry run, nothing is written' if args.dry_run else 'migrating'}: {root}{RESET}")
    for note in plan["notices"]:
        print(f"  {YELLOW}note{RESET}  {note}")
    if args.dry_run and (git_problem or dirty):
        why = git_problem or f"the working tree is not clean ({len(dirty)} path(s))"
        print(f"  {YELLOW}warn{RESET}  {why}: a real run would refuse")
    if not plan["renames"] and not plan["rewrites"] and not plan["symlink"]:
        print(f"  {GREEN}ok{RESET}    nothing to migrate")
        return 0

    _print_migration(plan, "would" if args.dry_run else "did  ")
    print()
    for line in migration_summary(plan):
        print(f"  {line}")
    print()
    if args.dry_run:
        print("  Run again without --dry-run to apply. Nothing is committed either way.")
        return 0

    apply_migration(plan)
    leftover = plan_migration(root, new_base, excludes, defaults)
    if leftover["rewrites"] or leftover["renames"]:
        print(f"  {RED}FAIL{RESET}  the migration left changes still to make: this is a bug")
        return 1
    print(f"  {GREEN}ok{RESET}    migrated; no commit was made")
    print("  next, from this layer (see docs/migrating-from-heimathafen.md):")
    print("    just link && just install-hooks && just doctor   # then review `git status` and commit")
    return 0


# ------------------------------------------------------------------------------------------- main


def main() -> int:
    p = argparse.ArgumentParser(prog="gwk")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (
        ("frontmatter", cmd_frontmatter),
        ("links", cmd_links),
        ("paths", cmd_paths),
        ("sensitive", cmd_sensitive),
        ("symlinks", cmd_symlinks),
        ("direction", cmd_direction),
        ("publishable", cmd_publishable),
        ("link", cmd_link),
        ("imports", cmd_imports),
    ):
        sub.add_parser(name).set_defaults(func=fn)

    cs = sub.add_parser("check-subject"); cs.add_argument("subject"); cs.set_defaults(func=cmd_check_subject)
    sub.add_parser("check-log").set_defaults(func=cmd_check_log)
    cm = sub.add_parser("commit-message")
    cm.add_argument("type"); cm.add_argument("scope"); cm.add_argument("message")
    cm.set_defaults(func=cmd_commit_message)

    sp = sub.add_parser("spec-check"); sp.add_argument("slug"); sp.set_defaults(func=cmd_spec_check)
    np = sub.add_parser("new-project"); np.add_argument("slug"); np.set_defaults(func=cmd_new_project)
    mp = sub.add_parser("memory-scan"); mp.add_argument("name"); mp.set_defaults(func=cmd_memory_scan)
    mm = sub.add_parser("map"); mm.add_argument("--check", action="store_true"); mm.set_defaults(func=cmd_map)
    sub.add_parser("entry").set_defaults(func=cmd_entry)
    mg = sub.add_parser("migrate-from-heimathafen",
                        help="rewrite one private layer from the heimathafen names to groundwork")
    mg.add_argument("layer", help="the layer's directory")
    mg.add_argument("--dry-run", action="store_true",
                    help="print the full change list and counts, write nothing")
    mg.add_argument("--base", help="the new base clone for .groundwork/base "
                                   "(default: the base this script belongs to, if the link names an old base)")
    mg.add_argument("--exclude", action="append", metavar="GLOB",
                    help="keep matching files as written (repeatable). A glob without a '/' matches "
                         "the file name at any depth, one with a '/' the path from the layer root; "
                         "'*' also matches '/'")
    mg.add_argument("--no-default-excludes", action="store_true",
                    help="also rewrite dated records (SESSION_LOG.md and *-YYYY-MM-DD*.md), "
                         "which are kept as written by default")
    mg.set_defaults(func=cmd_migrate)
    nl = sub.add_parser("new-layer"); nl.add_argument("path"); nl.add_argument("--name")
    nl.add_argument("--author-name"); nl.add_argument("--author-email")
    nl.set_defaults(func=cmd_new_layer)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
