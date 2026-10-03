---
title: "Derive tests from the code surface, not only from the acceptance criteria"
type: "rule"
category: "philosophy"
---

Acceptance criteria describe **what an issue promised**. They do not describe **what the code now
does**. Testing only from criteria leaves every surface the issue added incidentally — plumbing,
wiring, glue — completely unexercised, and that surface ships looking fine because nothing ever ran
it.

Before an issue closes, enumerate what it *added* and confirm each piece has been executed at least
once with real inputs. That enumeration comes from the code, not from the issue.

**Why:** a command-line tool dropped a bootstrap dependency, which required adding seven CLI
commands so the project could still manage itself. Its acceptance criteria were about the stability
contract and the dependency — they never said "every command works." Tests were written from those
criteria. The refusal paths of the new commands were covered; the success paths were not.

Four defects shipped in one release, every one reachable by simply running the command:

- The create-item command called its internal builder with the arguments in the wrong order, missing two required
  keyword arguments, and passing a milestone **id** where a **key** was expected — three errors in
  a single call.
- The unclaim command was missing a required keyword argument.
- Invalid input to the create-item command exited **70** (`the tool broke`) instead of **1** (`a rule
  declined`), so a caller could not tell a missing label from a crash.
- The **first** item in a fresh repository could not be created at all: the key prefix was
  inferred from existing keys, and there were none — which made adoption impossible for exactly the
  repositories adoption exists for.

**Confirmed again, independently** — and the second round is worse, because by then
1,661 tests were passing. Closing an issue by actually merging it through the tool found two more:

- The tool's merge command performed a **local** merge into a protected branch. It could never be pushed, so the work
  sat unreachable in one checkout while the pull request stayed open.
- Its finish command then accepted it: it checks "is the branch contained in the base", answered that against
  the **local** ref, and moved the issue to `done` — a status defined as *verified on the base* —
  while the remote base did not contain the change.

Both are on the single most-exercised path the tool has. Neither is exotic. Neither had a test,
because every test merged into an unprotected fixture branch, which is the one situation the real
repository is never in.

None was an edge case. All four were found within two minutes of installing the tool and using it
on a new project, and none was reachable by any test that existed. It is the same shape as the
problem that motivated replacing that tool: a surface nobody exercised, trusted because it
looked fine.

**How to apply:**

1. **Start from the diff, not the issue.** List every command, function, flag, branch and error
   path the change introduced. That list is the test inventory; the acceptance criteria are a
   *subset* of it, never the whole.
2. **Every entry point gets a success-path test**, not only refusals. Refusal tests are easy to
   write and give a false sense of coverage — they prove the guard, never the thing being guarded.
   A command whose success path is never exercised is a command nobody has run.
3. **Write a completeness guard, not just tests.** Enumerate the surface programmatically (walk the
   parser, the registry, the dispatch table) and assert every entry has coverage, so the *next*
   addition fails loudly instead of being forgotten. See `[[deliberate-break-proofs]]` — the guard
   itself must be proven to fire.
4. **Run it as a user would, once, before closing.** Install the artifact, use it on something that
   is not the development repository. Development repositories are pre-populated and hide every
   first-run and empty-state defect — three of the four above only appear on a fresh project.
5. **Ask whose workflow is not yours.** A surface can be fully exercised and still only ever
   tested in one *situation*. that tool was built by one person using one identity, so an
   issue's assignee never changed hands — and the tool turned out to have no way to reassign one
   at all, which makes it unusable by a team of two. The single-user path worked perfectly and hid
   the multi-user one entirely. Where a feature involves people, roles, permissions or time zones,
   the development repository is the least representative sample available.
6. **Prefer over-testing to missing a test.** A duplicated test costs a few seconds per run. A
   missing one costs a release. When unsure whether something is already covered, write it again.
7. **Test the entry point, not only the function behind it.** The command a person actually runs
   is the part that goes untested, because a test finds it easier to import the function and call
   it. Everything between — argument parsing, path resolution, the output the person reads, the
   exit code — is then covered by nothing. Both defects in that tool's map generator lived in
   its `__main__` block, invisible while the function it called was thoroughly tested. If the
   surface is a CLI, at least one test must run it as a subprocess and read what came back.
8. **Test the configuration you actually run in, not the one that is easy to set up.** A fixture
   branch with no protection, a repository with no history, a directory inside the repo — each is
   the convenient case and each is the one situation production is never in. Name the difference
   between the fixture and reality, then write the test for reality.
9. **Distinguish refusal from fault deliberately** at every entry point. Bad input from a caller is
   a refusal; a broken tool is a fault. Getting this wrong is invisible to a human reader and
   breaks every automated caller.

Complements `[[verify-before-claiming-done]]` (the claim-side discipline) and
`[[silence-is-not-evidence-a-system-works]]` (a green signal that asserts nothing). Reducing how
much surface exists in the first place is `[[reduce-testable-surface]]`.
