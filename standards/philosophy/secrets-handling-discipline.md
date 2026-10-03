---
title: "Secrets handling: never hand-extract, never inline, never hardcode"
type: "rule"
category: "philosophy"
---

Regardless of which secrets-management tool (or none) a given project uses, these are non-negotiable:

1. **Never hand-extract a credential from another tool's local config.** Don't read a token off disk out of a CLI's own config file (e.g. pulling a git host's API token out of a git CLI's stored credentials) to use it for something else. If a tool has its own sanctioned way to act on your behalf (its own CLI commands, its own auth flow), use that instead of reaching around it for the raw credential.
2. **Never pass a secret as a literal command-line argument.** It lands in shell history and session transcripts in cleartext. Route it through an environment variable via command substitution, a config file the command reads itself, or an interactive prompt — never as inline text in the command you run.
3. **Never commit a secret**, and never paste a raw secret value into a chat/agent transcript to move it between hosts or contexts — use whatever channel the project's actual secrets flow uses (a secrets manager, a direct host-to-host channel that never lands on the orchestrating machine), or ask the human to move it themselves.

4. **Never let a secret reach a check, a log line, or an error you print.** Checking whether a
   credential is *set* must never expand its *value*, and a service must never be sent a token that
   does not belong to it.
5. **Never print a raw response body from an authenticated request.** Services echo what they were
   sent. An error body is one of the most common places a credential resurfaces.

## The two leaks that produced rules 4 and 5

Both happened on 2026-08-30, in one session, and each cost a token rotation.

**Shell default-expansion prints the value.** This looks like a presence check and is not:

```bash
echo "token: ${CI_TOKEN:-absent}"     # prints the TOKEN when it is set
```

`${VAR:-default}` substitutes the default only when `VAR` is empty. When it is set — the normal case
— it substitutes **the secret**. Safe forms:

```bash
[ -n "${VAR:-}" ] && echo "token: present" || echo "token: absent"
echo "token: ${VAR:+present}"                  # :+ inverts, and never emits the value
```

**A token sent to the wrong service comes back in the error.** A CI token was sent as an
`Authorization` header to a *different* service that shared the same hostname family. It rejected the
request and included the offending header in its error body, which was then printed. Two rules fall
out: a credential is scoped to the service that issued it and goes nowhere else, and the body of a
failed authenticated request is never displayed — check the status code.

**Why:** every one is an avoidable exposure surface with a real, low-cost alternative — the discipline is what actually prevents leaks, not which specific tool happens to be storing secrets for a given project. Per-project secret storage (a dedicated secrets manager, environment-based config, whatever fits that project's deployment model) is a per-project decision; this discipline applies regardless of that choice.
