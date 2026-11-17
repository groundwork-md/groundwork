---
title: "Confidential documents: let an agent work on them without any value reaching the model provider"
type: "reference"
category: "confidential"
tags: [workflow, privacy, secrets, local-model]
---

# Working with confidential documents

How an agent helps with tax papers, bank statements, identity documents and contracts while the
values in them stay on the machine. The principle is
`standards/philosophy/confidential-values-stay-local.md`; the rules that apply to any secret are
[[secrets-handling-discipline]]. This is the process.

The pieces ship in `claude/skills/confidential/`: the `confidential.py` command, a guard hook and
the skill note. **Nothing here is active until a layer opts in.**

## The idea in one paragraph

A **local model** (anything on localhost that serves `/v1/chat/completions` and can return JSON)
reads a document and extracts. The values go into a **local encrypted store** under names such as
`ACME_TAX_ID`. The **cloud agent** only ever works with those names: it writes `{{ACME_TAX_ID}}` in
files and scripts. A local **fill-in** step writes the real values into an **output directory** the
person opens themselves. Everything the agent is shown passes a **leak filter** first.

## Opting in

A layer adds a `[confidential]` table to its `groundwork-layer.toml`. The highest-ranked layer that
has the table wins (the layers are read from `~/.claude/groundwork/ROOTS`, which `just link` writes
lowest rank first). `--config FILE` or the environment variable `GWK_CONFIDENTIAL_CONFIG` names a
TOML file with the same keys and overrides that. Without `enabled = true`, every command refuses
and the guard allows everything.

```toml
[confidential]
enabled       = true
endpoint      = "http://127.0.0.1:8080/v1/chat/completions"   # must be on localhost
model         = "local-extractor"
store         = "~/confidential/store.bin"
output_dir    = "~/confidential/filled"
store_backend = "keychain"            # dpapi | keychain | plain (plain is for tests only)
text_command  = ["pdftotext", "-layout", "{in}", "-"]          # turns a non-text file into text on stdout
image_command = ["pdfpages", "{in}", "{out}"]                   # optional: page images of a scanned PDF into {out}
label_only    = ["identity"]          # categories for which the agent gets only type and date
timeout_s     = 120
request_options = { reasoning_effort = "none" }   # optional; see the table
detectors     = [
  # a layer adds the formats of its own jurisdiction; the base stays neutral
  { kind = "case-ref", regex = "ACME-\\d{6}" },
]
```

| key | meaning |
| --- | --- |
| `enabled` | `true` turns the feature on |
| `endpoint`, `model` | the local model; the endpoint host must be `127.0.0.1`, `localhost` or `::1` |
| `store` | where the store lives (with `keychain`, it only identifies the keychain items) |
| `output_dir` | the only place `render` writes real values; the agent is kept out of it |
| `store_backend` | `dpapi` (Windows, user scope), `keychain` (macOS `security`), `plain` (unencrypted JSON, warns, tests only); the default is the platform's own, and on other systems it must be set |
| `text_command` | argv template for non-text files, `{in}` is the file; `.txt`, `.md` and `.csv` are read directly |
| `image_command` | optional argv template that writes a document's page images (`.png`, `.jpg`, `.webp`) into the folder `{out}`; used when `text_command` yields almost no text (a scan or photo PDF). Needs a model with vision |
| `label_only` | document categories whose summary is withheld |
| `detectors` | extra `{kind, regex}` findings, matched in ingestion and in the filter |
| `timeout_s` | for the model, the text command and `exec` |
| `request_options` | optional table merged into the model request, for runtime switches such as turning off a model's reasoning mode (`reasoning_effort = "none"`); it may not set `model`, `messages` or `response_format` |

Two runtime defaults matter. A model with a reasoning mode can spend its whole output budget
thinking and return a cut-off reply, which `ingest` reports as cut off and stores nothing from; turn
the mode off with `request_options` when the runtime supports it. And many runtimes start with a small
context window and silently drop the end of a long document: set the runtime's context length well
above the longest document you ingest.

## The process

1. **Opt in** (above) and wire the guard (below). Add values you already know with
   `confidential.py store add NAME --kind K --from-stdin`; the value comes from stdin or
   `--from-file`, never from an argument.
2. **Ingest** a document: `confidential.py ingest FILE`. The text is extracted (directly or with
   `text_command`; an image, or a PDF without a text layer through `image_command`, is first transcribed
   page by page by the local model, which needs vision), deterministic detectors run (IBAN with checksum, e-mail, phone-like numbers, `0x`
   addresses, bech32 addresses, long digit runs, money amounts with a currency, plus the layer's own),
   and the local model returns category, date, title, the sensitive items and a summary. New values go
   into the store; a value already stored keeps its name. Stored values are replaced by placeholders in
   the summary and the title, the leak filter runs, and **only the filtered result is printed**:
   category, date, title, summary, and the names added or reused. For a `label_only` category only
   category and date are printed.
3. **Stop conditions.** A document that looks like it holds a seed phrase is not read by the model,
   nothing is stored, and the output is `seed-phrase suspected in FILE`. If the model cannot be
   reached, nothing is stored and nothing derived from the file is printed.
4. **Use the names.** Either
   - **fill a template:** the agent writes a file with `{{NAME}}` placeholders and runs
     `confidential.py render TEMPLATE [OUT]`. It refuses to write outside `output_dir` and prints only
     `wrote <path>; filled n; missing: [names]`; or
   - **compute locally:** the agent writes a script that reads values through
     `from confidential import value` and runs it with `confidential.py exec -- CMD...`. The script gets
     no value in its environment or arguments, and its combined output passes the filter, so it should
     print verdicts and counts.
5. **Review.** The person opens `output_dir` and checks the filled document. Nothing the agent can
   read is in there.
6. **Deliver as a case.** A task arrives as a folder of inputs and leaves as a folder of results. File
   the inputs, the reply and its attachments together in the layer's archive as one case folder,
   numbered in the order things happened, each copy checksum-verified. Then replace the person's task
   folder with a result folder holding everything needed to act (the reply ready to send, the
   attachments named as they will be attached, a short note on what to expect), and move the task
   folder to the basket once the archive copies are confirmed. A result is never only a chat message.

`confidential.py filter` reads stdin and echoes it or prints `BLOCKED: n matches (kinds: ...)` and exits
1; use it on anything else that is about to be shown to the agent. `confidential.py store list` shows
names, kinds and shapes only, and never a value. `store add` and `store remove` are for the person; the
agent may use `store list` and `store rename`.

## The guard hook

`claude/skills/confidential/hooks/guard.py` is a Claude Code `PreToolUse` hook. It denies a Bash,
Read, Edit, Write, Grep, Glob or NotebookEdit call whose input names the configured `store` or
`output_dir` (case-insensitive, either slash style), and a Grep or Glob that starts above them. The one
exception is a Bash command that runs the skill's own `confidential.py` with an allowed subcommand and
names only `output_dir`. A broken config makes it print a notice and let the call through instead of
blocking every tool.

Wire it in the layer's Claude Code settings file, `settings.json` in its `claude/` directory (JSON has no comments, so the notes follow the block):

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        // every tool the guard understands; an empty or "*" matcher also works
        "matcher": "Bash|Read|Edit|Write|Grep|Glob|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            // the skill is assembled into ~/.claude/skills/ by `just link`
            "command": "python3 ~/.claude/skills/confidential/hooks/guard.py"
          }
        ]
      }
    ]
  }
}
```

The hook contract is Claude Code's: the event arrives as JSON on stdin with `tool_name` and
`tool_input`; exit code 2 blocks the call and sends stderr to the agent; exit 0 with no output lets it
proceed; any other exit code is a visible, non-blocking error. Re-check it against the current Claude
Code hooks documentation when Claude Code is upgraded.

## Where it runs

The scripts run on the machine that holds the store, and the local model must be on that machine's
localhost. When the store lives on another machine, the agent reaches it over `ssh`, for example
`ssh host 'python3 ~/.claude/skills/confidential/scripts/confidential.py ingest FILE'`. The guard matches
paths in the text of a command, so it covers an `ssh` command string too. The same holds for the other
side: the leak filter runs where the output is produced, before it comes back over the connection.

## Limits

- The guard and the filter catch **accidents**, not a hostile agent: commands run as the user
  (`standards/philosophy/confidential-values-stay-local.md`).
- The filter ignores stored values shorter than four characters (they would block everything) and
  matches digits-only forms only from eight digits. A value the person never stored and no detector
  recognises is not caught; add a layer detector for formats you rely on.
- The document is sent whole to the local model, so its context window bounds the document size.
- Recovery and seed phrases are never stored (see the principle note).
