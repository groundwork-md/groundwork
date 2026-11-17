#!/usr/bin/env python3
"""PreToolUse hook: keep the agent away from the confidential store and the output directory.

Contract (Claude Code hooks): the event arrives as JSON on stdin with `tool_name` and `tool_input`;
exit 2 blocks the call and shows stderr to the agent; exit 0 with no output lets it proceed; any
other exit is a visible but non-blocking error. This guard exits 2 to deny.

It denies any Bash, Read, Edit, Write, Grep, Glob or NotebookEdit call whose input names the
configured `store` or `output_dir` path (case-insensitive, either slash style), except a Bash command
that runs this skill's own `confidential.py` with an allowed subcommand and names only `output_dir`.
It matches paths in text, so an `ssh host '...'` command string is covered too.

This protects against accidental exposure, not against a hostile agent: commands run as the user.
"""

import json
import os
import re
import sys

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "scripts")
sys.path.insert(0, SCRIPTS)

import confidential  # noqa: E402

#: Subcommands the agent may run while naming the output directory. `store add` and `store remove`
#: are left to the user.
OWN_COMMAND = re.compile(
    r"skills/confidential/scripts/confidential\.py['\"]?\s+(?:--config\s+\S+\s+)*"
    r"(?:store\s+(?:list|rename)|config|ingest|filter|render|exec)(?![\w-])")


def norm(text):
    return re.sub(r"/{2,}", "/", text.replace("\\", "/").casefold())


def variants(path):
    """Every spelling of PATH worth matching in a command string."""
    forms = {norm(path).rstrip("/")}
    for candidate in (path, os.path.realpath(path)):
        n = norm(candidate).rstrip("/")
        forms.add(n)
        home = norm(os.path.expanduser("~")).rstrip("/")
        if n.startswith(home + "/"):
            rest = n[len(home):]
            forms.update(("~" + rest, "$home" + rest, "${home}" + rest))
        if re.match(r"[a-z]:/", n):
            forms.update(("/" + n[0] + n[2:], "/mnt/" + n[0] + n[2:]))
    return {f for f in forms if f}


def references(text, forms):
    return any(re.search(re.escape(f) + r"(?![\w-])", text) for f in forms)


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for item in node.values():
            yield from strings(item)
    elif isinstance(node, list):
        for item in node:
            yield from strings(item)


def is_ancestor(candidate, protected_forms):
    base = norm(os.path.abspath(os.path.expanduser(candidate))).rstrip("/")
    return bool(base) and any(f == base or f.startswith(base + "/") for f in protected_forms)


def decide(event, cfg):
    """A reason string to deny with, or None to allow."""
    store, out = variants(cfg["store"]), variants(cfg["output_dir"])
    tool, tool_input = event.get("tool_name", ""), event.get("tool_input") or {}
    text = norm("\n".join(strings(tool_input)))

    if tool in ("Grep", "Glob"):
        base = tool_input.get("path") or event.get("cwd") or ""
        literal = re.split(r"[*?\[{]", str(tool_input.get("pattern", "")))[0] if tool == "Glob" else ""
        for candidate in (base, literal):
            if candidate and is_ancestor(candidate, store | out):
                return "this search would reach the confidential store or output directory"

    if tool == "Bash":
        for segment in re.split(r"[;&|\n]+", text):
            if references(segment, store):
                return "this command names the confidential store path"
            if references(segment, out) and not OWN_COMMAND.search(segment):
                return ("this command names the confidential output directory; run the skill's own "
                        "confidential.py (render, exec, filter, ingest, config, store list|rename) instead")
        return None

    if references(text, store | out):
        return "this call names the confidential store or output directory; use the skill's commands"
    return None


def main():
    try:
        event = json.load(sys.stdin)
        cfg = confidential.load_config()
    except Exception as err:  # visible, non-blocking: a broken config must not lock every tool
        print(f"confidential guard could not start ({type(err).__name__}); not guarding this call", file=sys.stderr)
        return 1
    if not cfg.get("enabled") or not cfg.get("store") or not cfg.get("output_dir"):
        return 0
    reason = decide(event, cfg)
    if reason:
        print(f"Blocked by the confidential guard: {reason}.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
