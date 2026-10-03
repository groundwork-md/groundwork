---
title: "Separate verification from deployment, and never gate on a signal you cannot decompose"
type: "rule"
category: "philosophy"
---

"CI/CD" is one phrase for two things that behave oppositely. Treating them as one signal is fine
right up until a deployment exists, and then it is a correctness bug rather than an imprecision.

| | **verification** | **deployment** |
|---|---|---|
| When | before merge, on push and pull request | after merge, on a tag or a protected branch |
| Gates | the merge | **nothing** — it is downstream of the decision |
| A failure means | this change is wrong | production is broken |
| Re-running is | always safe | possibly a second deploy |
| Stale when | the branch moved | something else deployed |
| Right response to failure | do not merge | **a new bug issue** |

**The concrete bug:** a failed deployment blocks an *issue from being finished*. That is wrong — the
merge already happened, and a broken deployment is new work, not evidence the old work is unfinished.
The same conflation puts "re-run" in front of a person for a pipeline that may deploy twice.

## Never gate on a signal you cannot decompose — silently

The general principle, of which the above is one case.

A combined verdict — one status covering several pipelines — is safe to gate on. What is unsafe is
**calling it something more specific than it is.** "Verification passed" and "a combined verdict of
unknown composition was green" are different claims, and only one of them is true.

So:

1. **Classify the signal** — `verification`, `deployment`, `unknown`.
2. **`unknown` still gates.** Refusing to gate on an undecomposable signal is strictly less safe
   than gating on everything. The fix is honesty, not permissiveness.
3. **Say which you got.** The person deciding needs to know whether the green light covered what
   they think it covered.
4. **Never render "cannot see" as "nothing ran".** They read alike and mean opposite things —
   someone told "no runs" concludes CI is not configured, and merges.

## Where to put the distinction when the tooling cannot carry it

Often the tooling genuinely cannot decompose the signal. A forge that aggregates every pipeline into
one per-commit status is the common case; reading the CI service directly may cost a property you
are not willing to give up, such as holding no credentials.

When that happens, **do not build the decomposition anyway and do not pretend the problem is
absent.** In order of preference:

1. **Push the distinction to the producer.** One named status context per pipeline kind, published
   by the pipeline itself, so the consumer reads it where it already reads. Usually the right answer
   and usually overlooked.
2. **Record it in the specification and the vocabulary first**, so the wrong thing does not get
   built while the mechanism is blocked. Concepts are cheap; the code that assumed one signal is not.
3. **Report the limitation as a property, not as an apology.** "This forge does not expose individual
   runs; the verdict is the whole signal" is a correctness statement, and should read as one.

**Why:** a merge gate built on a single aggregated verdict is correct only while nothing deploys,
and that is an accident of a project being young, not a design. Record the split in the spec and
glossary before the first deployment exists, so the code never assumes one signal.

Related: `[[silence-is-not-evidence-a-system-works]]` — a green signal that asserts nothing is the
same failure one layer down.
