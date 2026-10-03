---
title: "New repos cause permission-storm hangs that freeze rails"
type: "hazard"
category: "wave-dispatch"
---

**Symptom:** a background subagent freezes permanently mid-tool-call, unreachable by `SendMessage`. Root cause: **allowlist history per repo**, not a machine fault. In an established repo almost every command matches an existing allowlist entry, so no approval dialog appears. In a brand-new repo, essentially every path-specific command is novel and requests approval — run several rails concurrently and those requests race, a newer request supersedes a pending one, and the superseded caller never gets an answer.

Allowlist matching is literal: an allowed single command does not cover a compound (`cmd1; cmd2`), and a path-specific allow does not cover the same command against a different path.

**Fix:** pre-populate `<repo>/.claude/settings.json` with the command patterns that repo's work actually needs, before dispatching rails into a young repo. (A `fewer-permission-prompts`-style skill can generate this from transcripts.)

**Hits the main/orchestrating session too**, not only rails — any command reaching *outside* the young repo's own path (e.g. reading a file elsewhere) can storm identically. Outs: use Read/Grep/Glob for anything outside the repo (never prompts), or a genuinely read-only Bash call with sandbox disabled explicitly. Don't "fix" this by widening a repo allowlist to cover unrelated global paths.

**Also effective:** keep concurrency modest while a repo is young; prefer absolute-path git/env invocations over `cd X && ...` compounds; ban Bash entirely for research-only rails (Read/Glob/Grep never prompt); never re-run a version check an orchestrator already verified. Note instruction-only "do not use Bash" is not enforcement — rails self-report stray shell calls anyway even when explicitly told not to; the real fix is removing the need (pre-create output dirs, pre-approve the few commands a rail predictably wants).

**Detecting a frozen rail:** a `SendMessage` reply is NOT a liveness check. A frozen rail's message queues for a tool round that never comes; a merely-idle rail's message returns "resumed from transcript" — the *second* one is the sign of a reachable agent, which is backwards from how it reads intuitively. Detect a freeze by `stat`-ing the rail's actual transcript file mtime (not a symlinked `.output` path, which reports the symlink's own metadata) and comparing against siblings known to have finished later. Recover with a scoped stop mechanism, never a PID or pattern kill (see `never-kill-by-pid-or-pattern.md`).
