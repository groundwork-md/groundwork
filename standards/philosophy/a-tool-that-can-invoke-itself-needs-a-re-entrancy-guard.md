---
title: "A task runner that can invoke itself needs a re-entrancy guard, not a careful author"
type: "rule"
category: "philosophy"
---

An aggregate command — `just doctor`, `hatch run gates`, `make check` — usually works by calling the
project's other commands. The moment one of those resolves back to the aggregate, it calls itself,
and each call calls itself again. This is not a slow failure. It is exponential, and it takes the
machine down before anything prints.

**Guard structurally. Do not rely on the call graph staying acyclic**, because the aggregate is
exactly the command people extend, and the resolution that closes the loop is usually indirect: a
recipe name shadowed by a dependency, a script entry that shares a name with the aggregate, a task
file imported from somewhere that defines the same target.

```python
REENTRY_ENV = "PROJECT_GATES_RUNNING"

if os.environ.get(REENTRY_ENV):
    print(f"refusing: {REENTRY_ENV} is set, so the gates are already running.", file=sys.stderr)
    return 1

subprocess.run([...], env={**os.environ, REENTRY_ENV: "1"})
```

Three properties matter and are easy to get wrong:

1. **Check before doing any work**, including before platform or argument validation. A guard that
   runs after a slow check still forks.
2. **Set the variable on the child's environment**, not the parent's. Mutating the parent leaks the
   flag to unrelated commands in the same shell.
3. **Refuse loudly.** Exiting silently makes the guard indistinguishable from success, and someone
   will later "fix" the aggregate by removing it.

**Why:** a command-line tool's aggregate `gates` command spawned roughly 705 processes and had to be stopped
with `pkill -9`. The first fix patched the wrong function — the one the author had read — while the
real runner resolved a differently-named entry point that still recursed. **Two attempts to fix it
by reasoning about the call graph both failed**; only the environment guard worked, because it does
not depend on knowing how the call was reached.

That is the general shape: when a failure comes from a path you did not know existed, the fix has to
be one that does not require knowing the path. See
`[[debugging-escalation-after-repeated-failures]]`.

**How to apply:** any command that runs other commands of the same project gets the guard when it is
written, not after the first incident. It is four lines, and the incident costs a machine.
